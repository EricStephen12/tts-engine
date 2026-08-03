from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("TTS_API_KEYS", "test-key")
os.environ.setdefault("TTS_LOG_JSON", "false")


class FakeKokoro:
    """Deterministic stand-in for kokoro_onnx.Kokoro used in fast unit/integration tests."""

    VOICES = ["af_heart", "af_bella", "am_eric"]

    def get_voices(self) -> list[str]:
        return list(self.VOICES)

    def create(self, text: str, voice: str, speed: float, lang: str):
        sample_rate = 24000
        # Deterministic pseudo-audio: duration scales with text length so
        # RTF/duration assertions in tests remain meaningful.
        duration_s = max(len(text) / 25.0, 0.05) / speed
        n_samples = int(sample_rate * duration_s)
        t = np.linspace(0, duration_s, n_samples, endpoint=False, dtype=np.float32)
        audio = 0.1 * np.sin(2 * np.pi * 220 * t).astype(np.float32)
        return audio, sample_rate


@pytest.fixture
def fake_model_manager(monkeypatch):
    from models import model_manager as mm_module

    mm_module.reset_model_manager()
    manager = mm_module.get_model_manager()
    manager._kokoro = FakeKokoro()
    manager._device = "cpu"
    yield manager
    mm_module.reset_model_manager()
