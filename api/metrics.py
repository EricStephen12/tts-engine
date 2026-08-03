"""Prometheus metric definitions shared across routes."""
from __future__ import annotations

from prometheus_client import Counter, Histogram

TTS_REQUESTS_TOTAL = Counter(
    "tts_requests_total", "Total TTS requests", ["endpoint", "status"]
)
TTS_CHARACTERS_TOTAL = Counter(
    "tts_characters_total", "Total characters synthesized"
)
TTS_LATENCY_SECONDS = Histogram(
    "tts_latency_seconds",
    "End-to-end synthesis latency in seconds",
    ["endpoint"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 20, 30),
)
TTS_REAL_TIME_FACTOR = Histogram(
    "tts_real_time_factor",
    "process_time / audio_duration (lower is better)",
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5),
)
