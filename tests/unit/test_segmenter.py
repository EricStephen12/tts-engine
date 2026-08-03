from text.segmenter import (
    PAUSE_PARAGRAPH_MS,
    PAUSE_SENTENCE_MS,
    segment,
)


def test_empty_text_returns_no_segments():
    assert segment("") == []
    assert segment("   ") == []


def test_single_sentence_has_no_trailing_pause():
    segs = segment("Hello there.")
    assert len(segs) == 1
    assert segs[0].pause_after_ms == 0


def test_multiple_sentences_get_sentence_pauses():
    segs = segment("First sentence. Second sentence.")
    assert len(segs) == 2
    assert segs[0].pause_after_ms == PAUSE_SENTENCE_MS
    assert segs[1].pause_after_ms == 0


def test_paragraph_break_gets_longest_pause():
    segs = segment("First paragraph.\n\nSecond paragraph.")
    assert len(segs) == 2
    assert segs[0].pause_after_ms == PAUSE_PARAGRAPH_MS
    assert segs[0].is_paragraph_break is True


def test_inline_pause_tag_overrides_default():
    segs = segment("Wait for it. [pause:900ms] Surprise!")
    assert any(s.pause_after_ms == 900 for s in segs)


def test_inline_pause_tag_is_clamped():
    segs = segment("Test. [pause:999999ms] End.")
    assert all(s.pause_after_ms <= 5000 for s in segs)
