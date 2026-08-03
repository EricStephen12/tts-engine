from __future__ import annotations

from pydantic import BaseModel, Field

from text.emotion import Emotion


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to synthesize. Supports inline [pause:500ms] tags.")
    voice: str | None = Field(default=None, description="Voice id, e.g. af_heart. Defaults to server config.")
    lang: str | None = Field(default=None, description="Kokoro language code, e.g. 'a' for American English.")
    emotion: Emotion = Field(default=Emotion.NEUTRAL)
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="Base speaking rate multiplier.")


class VoiceListResponse(BaseModel):
    voices: list[str]
    default_voice: str


class ErrorResponse(BaseModel):
    error_code: str
    message: str


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    device: str
    uptime_s: float


class StreamStartEvent(BaseModel):
    type: str = "start"
    sample_rate: int
    format: str = "pcm_s16le"
    channels: int = 1


class StreamAudioEvent(BaseModel):
    type: str = "audio_chunk"
    index: int
    text: str
    is_final: bool
    pause_after_ms: int
    data: str  # base64-encoded PCM16LE


class StreamEndEvent(BaseModel):
    type: str = "end"
    total_segments: int
    total_process_time_ms: float
