"""Text normalization: the first stage of the TTS pipeline.

Responsible for turning arbitrary user-supplied text into a clean string
that phonemizes well: expanding abbreviations, numbers, currency and
percentages, normalizing punctuation/whitespace, while leaving inline
control tags (`[pause:500ms]`) untouched for the segmenter to consume.
"""
from __future__ import annotations

import re

from num2words import num2words

_ABBREVIATIONS = {
    r"\bMr\.": "Mister",
    r"\bMrs\.": "Missus",
    r"\bMs\.": "Miss",
    r"\bDr\.": "Doctor",
    r"\bProf\.": "Professor",
    r"\bSt\.": "Saint",
    r"\bJr\.": "Junior",
    r"\bSr\.": "Senior",
    r"\bvs\.": "versus",
    r"\betc\.": "et cetera",
    r"\be\.g\.": "for example",
    r"\bi\.e\.": "that is",
    r"\bapprox\.": "approximately",
}

_CURRENCY_RE = re.compile(r"\$(\d[\d,]*)(?:\.(\d{2}))?")
_PERCENT_RE = re.compile(r"(\d+(?:\.\d+)?)\s?%")
_NUMBER_RE = re.compile(r"(?<![\w.])\d[\d,]*(?:\.\d+)?(?![\w])")
_WHITESPACE_RE = re.compile(r"[ \t]+")
_MULTI_NEWLINE_RE = re.compile(r"\n{3,}")

# Protects inline control tags like [pause:500ms] from number expansion.
_TAG_RE = re.compile(r"\[[a-zA-Z]+:[^\]]+\]")


def _expand_abbreviations(text: str) -> str:
    for pattern, replacement in _ABBREVIATIONS.items():
        text = re.sub(pattern, replacement, text)
    return text


def _number_to_words(match: re.Match[str]) -> str:
    raw = match.group(0).replace(",", "")
    try:
        if "." in raw:
            return num2words(float(raw))
        return num2words(int(raw))
    except (ValueError, OverflowError):
        return match.group(0)


def _expand_currency(match: re.Match[str]) -> str:
    dollars = match.group(1).replace(",", "")
    cents = match.group(2)
    try:
        dollars_words = num2words(int(dollars))
        dollar_unit = "dollar" if dollars == "1" else "dollars"
        if cents and int(cents) > 0:
            cents_words = num2words(int(cents))
            cent_unit = "cent" if cents == "01" else "cents"
            return f"{dollars_words} {dollar_unit} and {cents_words} {cent_unit}"
        return f"{dollars_words} {dollar_unit}"
    except (ValueError, OverflowError):
        return match.group(0)


def _expand_percent(match: re.Match[str]) -> str:
    value = match.group(1)
    try:
        words = num2words(float(value)) if "." in value else num2words(int(value))
        return f"{words} percent"
    except (ValueError, OverflowError):
        return match.group(0)


def normalize(text: str) -> str:
    """Normalize raw input text prior to segmentation and synthesis.

    This function is intentionally defensive: any expansion step that fails
    (e.g. an oddly formatted number) falls back to leaving the original
    substring untouched rather than raising, since Kokoro's phonemizer can
    usually still read raw digits reasonably well.
    """
    if not text:
        return text

    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2013", "-").replace("\u2014", "-")

    text = _expand_abbreviations(text)

    # Protect inline control tags from digit expansion below.
    protected: list[str] = []

    def _protect(match: re.Match[str]) -> str:
        protected.append(match.group(0))
        # Letters surround the index so _NUMBER_RE's word-boundary checks
        # never treat the digits inside the placeholder as a real number.
        return f"\x00TAG{len(protected) - 1}TAG\x00"

    text = _TAG_RE.sub(_protect, text)

    text = _CURRENCY_RE.sub(_expand_currency, text)
    text = _PERCENT_RE.sub(_expand_percent, text)
    text = _NUMBER_RE.sub(_number_to_words, text)

    def _restore(match: re.Match[str]) -> str:
        return protected[int(match.group(1))]

    text = re.sub(r"\x00TAG(\d+)TAG\x00", _restore, text)

    text = _MULTI_NEWLINE_RE.sub("\n\n", text)
    text = _WHITESPACE_RE.sub(" ", text)
    text = "\n".join(line.strip() for line in text.split("\n"))

    return text.strip()
