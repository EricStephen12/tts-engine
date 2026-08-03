"""Performance smoke tests.

These use the FakeKokoro fixture (not the real model) to validate the
*pipeline's own* overhead (normalization, segmentation, DSP, concatenation)
stays low. Real-model RTF/latency is measured separately via
`scripts/benchmark.py` against actual Kokoro weights.
"""
from __future__ import annotations

import time

import pytest

from inference.engine import TTSEngine

pytestmark = pytest.mark.performance


def test_pipeline_overhead_is_low_for_short_text(fake_model_manager):
    engine = TTSEngine(model_manager=fake_model_manager)
    start = time.perf_counter()
    engine.synthesize("This is a short benchmark sentence for latency testing.")
    elapsed_ms = (time.perf_counter() - start) * 1000
    # Generous ceiling: this only bounds our own DSP/orchestration overhead,
    # since FakeKokoro's "synthesis" is near-instant.
    assert elapsed_ms < 500


def test_pipeline_scales_reasonably_with_long_text(fake_model_manager):
    engine = TTSEngine(model_manager=fake_model_manager)
    long_text = "This is one sentence. " * 100

    start = time.perf_counter()
    result = engine.synthesize(long_text[:4900])
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert result.num_segments > 50
    # Should still process well under a second of orchestration overhead
    # even for near-max-length input, using the fake (instant) model.
    assert elapsed_ms < 3000
