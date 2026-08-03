import numpy as np

from audio.postprocess import (
    apply_gain,
    crossfade_concat,
    generate_silence,
    normalize_loudness,
)


def test_generate_silence_has_correct_length():
    silence = generate_silence(1000, 24000)
    assert len(silence) == 24000
    assert np.all(silence == 0)


def test_apply_gain_zero_is_noop():
    audio = np.array([0.1, 0.2, -0.1], dtype=np.float32)
    assert np.allclose(apply_gain(audio, 0), audio)


def test_apply_gain_boosts_amplitude():
    audio = np.array([0.1, 0.1, 0.1], dtype=np.float32)
    boosted = apply_gain(audio, 6.0)
    assert np.all(boosted > audio)


def test_apply_gain_clips_to_valid_range():
    audio = np.array([0.9, -0.9], dtype=np.float32)
    boosted = apply_gain(audio, 24.0)
    assert np.all(boosted <= 1.0) and np.all(boosted >= -1.0)


def test_normalize_loudness_handles_silence():
    silence = np.zeros(100, dtype=np.float32)
    result = normalize_loudness(silence)
    assert np.all(result == 0)


def test_crossfade_concat_shortens_by_overlap_duration():
    a = np.ones(1000, dtype=np.float32) * 0.1
    b = np.ones(1000, dtype=np.float32) * 0.2
    crossfade_ms = 10
    fade_n = int(24000 * crossfade_ms / 1000)
    result = crossfade_concat([a, b], sample_rate=24000, crossfade_ms=crossfade_ms)
    # Total length is len(a) + len(b) - overlap, since the crossfade window
    # blends (rather than appends) `fade_n` samples at the boundary.
    assert len(result) == 2000 - fade_n


def test_crossfade_concat_single_chunk_passthrough():
    a = np.ones(500, dtype=np.float32)
    result = crossfade_concat([a], sample_rate=24000)
    assert np.array_equal(result, a)


def test_crossfade_concat_empty_list():
    result = crossfade_concat([], sample_rate=24000)
    assert len(result) == 0
