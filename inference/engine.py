"""TTSEngine: orchestrates normalization -> segmentation -> per-segment
synthesis -> emotion/prosody shaping -> pause insertion -> concatenation.

Exposes both a blocking `synthesize()` (for the full-file REST endpoint)
and a generator-based `synthesize_stream()` (for the streaming endpoint),
so long text starts producing audio well before the entire input is done.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

import numpy as np

from audio.postprocess import (
    apply_gain,
    apply_pitch_shift,
    crossfade_concat,
    generate_silence,
    normalize_loudness,
)
from config.logging_config import get_logger
from config.settings import Settings, get_settings
from models.model_manager import ModelManager, get_model_manager
from text.emotion import get_profile
from text.normalizer import normalize
from text.segmenter import Segment, segment
from utils.exceptions import (
    EmptyTextError,
    InvalidEmotionError,
    InvalidVoiceError,
    SynthesisError,
    TextTooLongError,
)
from utils.timing import Timer

logger = get_logger(__name__)


@dataclass
class SegmentResult:
    index: int
    text: str
    audio: np.ndarray
    sample_rate: int
    pause_after_ms: int
    synth_ms: float
    is_final: bool


@dataclass
class SynthesisResult:
    audio: np.ndarray
    sample_rate: int
    audio_duration_s: float
    process_time_ms: float
    real_time_factor: float
    num_segments: int


class TTSEngine:
    def __init__(self, model_manager: ModelManager | None = None, settings: Settings | None = None):
        self._settings = settings or get_settings()
        self._model_manager = model_manager or get_model_manager()

    def _prepare_segments(self, text: str) -> list[Segment]:
        if not text or not text.strip():
            raise EmptyTextError("Input text must not be empty.")
        if len(text) > self._settings.max_text_length:
            raise TextTooLongError(
                f"Text length {len(text)} exceeds max_text_length="
                f"{self._settings.max_text_length}."
            )
        normalized = normalize(text)
        segments = segment(normalized)
        if not segments:
            raise EmptyTextError("Input text normalized to nothing synthesizable.")
        return segments

    def _validate_voice(self, voice: str) -> None:
        available = self._model_manager.list_voices()
        if voice not in available:
            raise InvalidVoiceError(
                f"Unknown voice {voice!r}. Available voices: {', '.join(available)}"
            )

    def _synthesize_segment(
        self, seg: Segment, voice: str, lang: str, emotion: str, speed: float
    ) -> tuple[np.ndarray, int, float]:
        try:
            profile = get_profile(emotion)
        except ValueError as exc:
            raise InvalidEmotionError(str(exc)) from exc
        effective_speed = round(speed * profile.speed_multiplier, 3)

        with Timer() as t:
            try:
                audio, sample_rate = self._model_manager.synthesize(
                    seg.text, voice=voice, speed=effective_speed, lang=lang
                )
            except Exception as exc:  # noqa: BLE001
                raise SynthesisError(f"Synthesis failed for segment: {exc}") from exc

            audio = np.asarray(audio, dtype=np.float32)
            if profile.pitch_shift_semitones:
                audio = apply_pitch_shift(audio, sample_rate, profile.pitch_shift_semitones)
            if profile.energy_gain_db:
                audio = apply_gain(audio, profile.energy_gain_db)
            audio = normalize_loudness(audio)

        return audio, sample_rate, t.elapsed_ms

    def synthesize(
        self,
        text: str,
        voice: str | None = None,
        emotion: str = "neutral",
        speed: float = 1.0,
        lang: str | None = None,
        validate_voice: bool = True,
    ) -> SynthesisResult:
        settings = self._settings
        voice = voice or settings.default_voice
        lang = lang or settings.default_lang

        if validate_voice:
            self._validate_voice(voice)

        segments = self._prepare_segments(text)

        with Timer() as total_timer:
            chunks: list[np.ndarray] = []
            sample_rate = settings.sample_rate
            for seg in segments:
                audio, sample_rate, _ = self._synthesize_segment(seg, voice, lang, emotion, speed)
                chunks.append(audio)
                if seg.pause_after_ms > 0:
                    chunks.append(generate_silence(seg.pause_after_ms, sample_rate))

            final_audio = crossfade_concat(chunks, sample_rate)

        audio_duration_s = len(final_audio) / sample_rate if sample_rate else 0.0
        process_time_s = total_timer.elapsed_ms / 1000.0
        rtf = (process_time_s / audio_duration_s) if audio_duration_s > 0 else 0.0

        logger.info(
            "synthesis_complete",
            characters=len(text),
            segments=len(segments),
            audio_duration_s=round(audio_duration_s, 3),
            process_time_ms=round(total_timer.elapsed_ms, 1),
            rtf=round(rtf, 3),
        )

        return SynthesisResult(
            audio=final_audio,
            sample_rate=sample_rate,
            audio_duration_s=audio_duration_s,
            process_time_ms=total_timer.elapsed_ms,
            real_time_factor=rtf,
            num_segments=len(segments),
        )

    def synthesize_stream(
        self,
        text: str,
        voice: str | None = None,
        emotion: str = "neutral",
        speed: float = 1.0,
        lang: str | None = None,
        validate_voice: bool = True,
    ) -> Iterator[SegmentResult]:
        settings = self._settings
        voice = voice or settings.default_voice
        lang = lang or settings.default_lang

        if validate_voice:
            self._validate_voice(voice)

        segments = self._prepare_segments(text)
        total = len(segments)

        for idx, seg in enumerate(segments):
            audio, sample_rate, synth_ms = self._synthesize_segment(seg, voice, lang, emotion, speed)
            yield SegmentResult(
                index=idx,
                text=seg.text,
                audio=audio,
                sample_rate=sample_rate,
                pause_after_ms=seg.pause_after_ms,
                synth_ms=synth_ms,
                is_final=(idx == total - 1),
            )
