"""DSP utilities: silence generation, pitch/gain shaping, and click-free
concatenation of synthesized segments.
"""
from __future__ import annotations

import numpy as np

_EPS = 1e-9


def generate_silence(duration_ms: float, sample_rate: int) -> np.ndarray:
    n_samples = int(round(sample_rate * duration_ms / 1000.0))
    return np.zeros(max(n_samples, 0), dtype=np.float32)


def apply_gain(audio: np.ndarray, gain_db: float) -> np.ndarray:
    if gain_db == 0:
        return audio
    factor = 10.0 ** (gain_db / 20.0)
    return np.clip(audio * factor, -1.0, 1.0).astype(np.float32)


def apply_pitch_shift(audio: np.ndarray, sample_rate: int, semitones: float) -> np.ndarray:
    if semitones == 0 or audio.size == 0:
        return audio
    import librosa

    shifted = librosa.effects.pitch_shift(
        y=audio.astype(np.float32), sr=sample_rate, n_steps=semitones
    )
    return np.clip(shifted, -1.0, 1.0).astype(np.float32)


def normalize_loudness(audio: np.ndarray, target_dbfs: float = -20.0) -> np.ndarray:
    """Simple RMS-based loudness normalization (fast, dependency-free)."""
    if audio.size == 0:
        return audio
    rms = np.sqrt(np.mean(np.square(audio)) + _EPS)
    current_dbfs = 20 * np.log10(rms + _EPS)
    gain_db = target_dbfs - current_dbfs
    # Avoid excessive amplification of near-silent buffers.
    gain_db = float(np.clip(gain_db, -24.0, 24.0))
    return apply_gain(audio, gain_db)


def add_background_noise(audio: np.ndarray, noise_level: float = 0.0) -> np.ndarray:
    """Add a very low ambient noise floor for a more human-sounding output."""
    if audio.size == 0 or noise_level <= 0.0:
        return audio

    noise_db = float(np.clip(-65.0 + noise_level * 30.0, -80.0, -40.0))
    noise_amp = 10.0 ** (noise_db / 20.0)
    noise = np.random.normal(0.0, noise_amp, size=audio.shape).astype(np.float32)
    return np.clip(audio + noise, -1.0, 1.0).astype(np.float32)


def crossfade_concat(chunks: list[np.ndarray], sample_rate: int, crossfade_ms: float = 8.0) -> np.ndarray:
    """Concatenate audio chunks (which may include silence) with a short
    equal-power crossfade at each boundary to avoid audible clicks.
    """
    chunks = [c for c in chunks if c.size > 0]
    if not chunks:
        return np.zeros(0, dtype=np.float32)
    if len(chunks) == 1:
        return chunks[0]

    fade_n = max(int(sample_rate * crossfade_ms / 1000.0), 1)
    result = chunks[0].astype(np.float32).copy()

    for chunk in chunks[1:]:
        chunk = chunk.astype(np.float32)
        n = min(fade_n, len(result), len(chunk))
        if n <= 1:
            result = np.concatenate([result, chunk])
            continue

        fade_out = np.sqrt(np.linspace(1.0, 0.0, n, dtype=np.float32))
        fade_in = np.sqrt(np.linspace(0.0, 1.0, n, dtype=np.float32))

        head = result[:-n]
        tail_mixed = result[-n:] * fade_out + chunk[:n] * fade_in
        rest = chunk[n:]

        result = np.concatenate([head, tail_mixed, rest])

    return result.astype(np.float32)
