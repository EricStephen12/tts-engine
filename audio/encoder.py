"""Audio encoding helpers for REST (full WAV) and streaming (raw PCM16)
responses.
"""
from __future__ import annotations

import base64
import io

import numpy as np
import soundfile as sf


def float32_to_pcm16_bytes(audio: np.ndarray) -> bytes:
    clipped = np.clip(audio, -1.0, 1.0)
    pcm16 = (clipped * 32767.0).astype("<i2")
    return pcm16.tobytes()


def to_wav_bytes(audio: np.ndarray, sample_rate: int) -> bytes:
    buffer = io.BytesIO()
    sf.write(buffer, audio, sample_rate, format="WAV", subtype="PCM_16")
    return buffer.getvalue()


def pcm16_to_base64(audio: np.ndarray) -> str:
    return base64.b64encode(float32_to_pcm16_bytes(audio)).decode("ascii")
