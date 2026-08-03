import pytest

from text.emotion import Emotion, get_profile


def test_neutral_profile_is_identity():
    profile = get_profile(Emotion.NEUTRAL)
    assert profile.speed_multiplier == 1.0
    assert profile.pitch_shift_semitones == 0.0
    assert profile.energy_gain_db == 0.0


def test_excited_is_faster_and_brighter_than_sad():
    excited = get_profile(Emotion.EXCITED)
    sad = get_profile(Emotion.SAD)
    assert excited.speed_multiplier > sad.speed_multiplier
    assert excited.pitch_shift_semitones > sad.pitch_shift_semitones


def test_accepts_string_value():
    profile = get_profile("happy")
    assert profile.speed_multiplier > 1.0


def test_invalid_emotion_raises():
    with pytest.raises(ValueError):
        get_profile("furious")
