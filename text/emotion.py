"""Heuristic emotion -> prosody mapping (v1).

Kokoro-82M has no native emotion embedding, so "emotion" here is
approximated by adjusting speaking rate, pitch, and energy on top of a
neutral voice rendering. This is documented as a known limitation --
see docs/ROADMAP.md for the planned v2 upgrade (an emotion-conditioned
model for acoustically distinct emotional deliveries).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Emotion(str, Enum):
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    EXCITED = "excited"
    CALM = "calm"


@dataclass(frozen=True)
class EmotionProfile:
    speed_multiplier: float
    pitch_shift_semitones: float
    energy_gain_db: float


_PROFILES: dict[Emotion, EmotionProfile] = {
    Emotion.NEUTRAL: EmotionProfile(1.00, 0.0, 0.0),
    Emotion.HAPPY: EmotionProfile(1.10, 1.5, 1.5),
    Emotion.EXCITED: EmotionProfile(1.18, 2.5, 3.0),
    Emotion.SAD: EmotionProfile(0.90, -2.0, -2.0),
    Emotion.CALM: EmotionProfile(0.92, -0.5, -1.0),
    Emotion.ANGRY: EmotionProfile(1.05, 0.5, 3.5),
}


def get_profile(emotion: str | Emotion) -> EmotionProfile:
    try:
        key = Emotion(emotion) if not isinstance(emotion, Emotion) else emotion
    except ValueError as exc:
        valid = ", ".join(e.value for e in Emotion)
        raise ValueError(f"Unknown emotion {emotion!r}. Valid values: {valid}") from exc
    return _PROFILES[key]
