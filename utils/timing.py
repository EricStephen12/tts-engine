"""Lightweight latency measurement helpers."""
from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Iterator


@dataclass
class Timer:
    """Context manager that records elapsed wall-clock time in milliseconds."""

    elapsed_ms: float = field(default=0.0, init=False)
    _start: float = field(default=0.0, init=False, repr=False)

    def __enter__(self) -> "Timer":
        self._start = time.perf_counter()
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.elapsed_ms = (time.perf_counter() - self._start) * 1000.0


@contextmanager
def measure(label: str = "") -> Iterator[Timer]:
    timer = Timer()
    with timer:
        yield timer
