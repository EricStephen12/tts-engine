"""Sentence/paragraph segmentation with human-like pause metadata.

This is what gives synthesized speech natural pacing: short pauses after
commas, longer pauses at sentence boundaries, and the longest pauses between
paragraphs -- plus support for an explicit `[pause:500ms]` inline tag so
callers can fine-tune pacing (e.g. dramatic beats in ad scripts).
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# Default pause durations (ms), tunable without code changes if needed later.
PAUSE_COMMA_MS = 150
PAUSE_SENTENCE_MS = 350
PAUSE_PARAGRAPH_MS = 600
PAUSE_MIN_MS = 0
PAUSE_MAX_MS = 5000

_INLINE_PAUSE_RE = re.compile(r"\[pause:(\d+)\s*ms\]", re.IGNORECASE)
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])")
_TRAILING_PUNCT_RE = re.compile(r"[,;:]\s*$")


@dataclass
class Segment:
    """A single synthesizable unit of text plus the pause that follows it."""

    text: str
    pause_after_ms: int
    is_paragraph_break: bool = False


def _split_sentences(paragraph: str) -> list[str]:
    parts = _SENTENCE_SPLIT_RE.split(paragraph.strip())
    return [p.strip() for p in parts if p.strip()]


def segment(text: str) -> list[Segment]:
    """Split normalized text into synthesis segments with pause metadata."""
    if not text or not text.strip():
        return []

    paragraphs = [p for p in text.split("\n\n") if p.strip()]
    segments: list[Segment] = []

    for p_idx, paragraph in enumerate(paragraphs):
        is_last_paragraph = p_idx == len(paragraphs) - 1
        sentences = _split_sentences(paragraph)

        for s_idx, sentence in enumerate(sentences):
            is_last_sentence = s_idx == len(sentences) - 1

            # Extract a trailing inline pause override, if present.
            inline_match = _INLINE_PAUSE_RE.search(sentence)
            override_ms: int | None = None
            if inline_match:
                override_ms = max(
                    PAUSE_MIN_MS, min(PAUSE_MAX_MS, int(inline_match.group(1)))
                )
                sentence = _INLINE_PAUSE_RE.sub("", sentence).strip()

            if not sentence:
                if override_ms is not None and segments:
                    segments[-1].pause_after_ms += override_ms
                continue

            if override_ms is not None:
                pause_ms = override_ms
            elif not is_last_sentence:
                pause_ms = PAUSE_SENTENCE_MS
            elif not is_last_paragraph:
                pause_ms = PAUSE_PARAGRAPH_MS
            else:
                pause_ms = 0

            segments.append(
                Segment(
                    text=sentence,
                    pause_after_ms=pause_ms,
                    is_paragraph_break=(is_last_sentence and not is_last_paragraph),
                )
            )

    return segments
