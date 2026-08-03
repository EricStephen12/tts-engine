"""Latency / RTF / memory benchmark for the TTS engine.

Run after downloading model weights:
    python scripts/benchmark.py

Writes a human-readable table to stdout and a machine-readable
`benchmark_results.json` in the project root.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

TEXTS = {
    "short (1 sentence)": "The quick brown fox jumps over the lazy dog.",
    "medium (1 paragraph)": (
        "Eixora helps creators generate high-converting UGC ad scripts in minutes. "
        "Our proprietary text to speech engine turns those scripts into natural, "
        "human sounding voiceovers without ever touching a third party API."
    ),
    "long (multi paragraph)": (
        "Welcome to Eixora. This is a longer passage meant to simulate a full "
        "voiceover script for a thirty second advertisement.\n\n"
        "It includes multiple sentences, a paragraph break, and varied punctuation "
        "such as commas, semicolons; and exclamation marks! This lets us measure "
        "how pacing and pause insertion behave across segment boundaries.\n\n"
        "Finally, we close with a call to action: try Eixora today, and hear the "
        "difference for yourself."
    ),
}


def _peak_memory_mb() -> float:
    try:
        import psutil

        return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
    except ImportError:
        return -1.0


def main() -> int:
    from inference.engine import TTSEngine
    from models.model_manager import get_model_manager

    manager = get_model_manager()
    manager.load()
    engine = TTSEngine(model_manager=manager)

    results = []
    print(f"{'Case':<28}{'Chars':>7}{'Audio(s)':>10}{'Time(ms)':>11}{'RTF':>8}{'xRealtime':>11}{'MemMB':>9}")
    print("-" * 90)

    # Warm-up run (excludes model/session first-call overhead from timings).
    engine.synthesize(TEXTS["short (1 sentence)"])

    for name, text in TEXTS.items():
        start = time.perf_counter()
        result = engine.synthesize(text)
        wall_ms = (time.perf_counter() - start) * 1000.0
        mem_mb = _peak_memory_mb()
        x_realtime = (result.audio_duration_s / (wall_ms / 1000.0)) if wall_ms > 0 else 0.0

        print(
            f"{name:<28}{len(text):>7}{result.audio_duration_s:>10.2f}"
            f"{wall_ms:>11.1f}{result.real_time_factor:>8.3f}{x_realtime:>11.2f}{mem_mb:>9.1f}"
        )
        results.append(
            {
                "case": name,
                "characters": len(text),
                "audio_duration_s": result.audio_duration_s,
                "wall_time_ms": wall_ms,
                "real_time_factor": result.real_time_factor,
                "x_realtime": x_realtime,
                "memory_mb": mem_mb,
                "device": manager.device,
            }
        )

    out_path = Path(__file__).resolve().parent.parent / "benchmark_results.json"
    out_path.write_text(json.dumps(results, indent=2))
    print(f"\nDevice: {manager.device}")
    print(f"Results written to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
