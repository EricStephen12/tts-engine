import json

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response, StreamingResponse

from api.metrics import (
    TTS_CHARACTERS_TOTAL,
    TTS_LATENCY_SECONDS,
    TTS_REAL_TIME_FACTOR,
    TTS_REQUESTS_TOTAL,
)
from api.middleware.auth import require_api_key
from api.middleware.rate_limit import limiter
from api.schemas.tts import TTSRequest
from audio.encoder import pcm16_to_base64, to_wav_bytes
from config.logging_config import get_logger
from config.settings import get_settings
from inference.engine import TTSEngine

router = APIRouter(prefix="/api/v1", tags=["tts"])
logger = get_logger(__name__)
_RATE_LIMIT = get_settings().rate_limit


def get_engine() -> TTSEngine:
    return TTSEngine()


@router.post("/tts", dependencies=[Depends(require_api_key)])
@limiter.limit(_RATE_LIMIT)
async def synthesize(request: Request, body: TTSRequest) -> Response:
    engine = get_engine()
    endpoint = "tts"
    try:
        result = engine.synthesize(
            text=body.text,
            voice=body.voice,
            emotion=body.emotion.value,
            speed=body.speed,
            lang=body.lang,
        )
    except Exception:
        TTS_REQUESTS_TOTAL.labels(endpoint=endpoint, status="error").inc()
        raise

    TTS_REQUESTS_TOTAL.labels(endpoint=endpoint, status="success").inc()
    TTS_CHARACTERS_TOTAL.inc(len(body.text))
    TTS_LATENCY_SECONDS.labels(endpoint=endpoint).observe(result.process_time_ms / 1000.0)
    TTS_REAL_TIME_FACTOR.observe(result.real_time_factor)

    wav_bytes = to_wav_bytes(result.audio, result.sample_rate)
    return Response(
        content=wav_bytes,
        media_type="audio/wav",
        headers={
            "X-Audio-Duration-S": f"{result.audio_duration_s:.3f}",
            "X-Real-Time-Factor": f"{result.real_time_factor:.3f}",
            "X-Segments": str(result.num_segments),
        },
    )


@router.post("/tts/stream", dependencies=[Depends(require_api_key)])
@limiter.limit(_RATE_LIMIT)
async def synthesize_stream(request: Request, body: TTSRequest) -> StreamingResponse:
    engine = get_engine()
    endpoint = "tts_stream"

    def event_stream():
        sample_rate_sent = False
        total_process_ms = 0.0
        segment_count = 0
        try:
            for seg in engine.synthesize_stream(
                text=body.text,
                voice=body.voice,
                emotion=body.emotion.value,
                speed=body.speed,
                lang=body.lang,
            ):
                if not sample_rate_sent:
                    yield json.dumps(
                        {"type": "start", "sample_rate": seg.sample_rate, "format": "pcm_s16le", "channels": 1}
                    ) + "\n"
                    sample_rate_sent = True

                total_process_ms += seg.synth_ms
                segment_count += 1

                yield json.dumps(
                    {
                        "type": "audio_chunk",
                        "index": seg.index,
                        "text": seg.text,
                        "is_final": seg.is_final,
                        "pause_after_ms": seg.pause_after_ms,
                        "data": pcm16_to_base64(seg.audio),
                    }
                ) + "\n"

            yield json.dumps(
                {"type": "end", "total_segments": segment_count, "total_process_time_ms": total_process_ms}
            ) + "\n"
            TTS_REQUESTS_TOTAL.labels(endpoint=endpoint, status="success").inc()
            TTS_CHARACTERS_TOTAL.inc(len(body.text))
            TTS_LATENCY_SECONDS.labels(endpoint=endpoint).observe(total_process_ms / 1000.0)
        except Exception as exc:  # noqa: BLE001
            TTS_REQUESTS_TOTAL.labels(endpoint=endpoint, status="error").inc()
            logger.error("stream_synthesis_failed", error=str(exc))
            yield json.dumps({"type": "error", "message": str(exc)}) + "\n"

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")
