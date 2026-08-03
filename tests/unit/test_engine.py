import pytest

from inference.engine import TTSEngine
from utils.exceptions import EmptyTextError, InvalidEmotionError, InvalidVoiceError, TextTooLongError


def test_synthesize_returns_audio(fake_model_manager):
    engine = TTSEngine(model_manager=fake_model_manager)
    result = engine.synthesize("Hello world. This is a test.")
    assert result.audio.size > 0
    assert result.sample_rate == 24000
    assert result.num_segments == 2
    assert result.audio_duration_s > 0


def test_synthesize_empty_text_raises(fake_model_manager):
    engine = TTSEngine(model_manager=fake_model_manager)
    with pytest.raises(EmptyTextError):
        engine.synthesize("   ")


def test_synthesize_too_long_raises(fake_model_manager):
    engine = TTSEngine(model_manager=fake_model_manager)
    with pytest.raises(TextTooLongError):
        engine.synthesize("word " * 2000)


def test_synthesize_invalid_voice_raises(fake_model_manager):
    engine = TTSEngine(model_manager=fake_model_manager)
    with pytest.raises(InvalidVoiceError):
        engine.synthesize("Hello.", voice="not_a_real_voice")


from utils.exceptions import EmptyTextError, InvalidEmotionError, InvalidVoiceError, TextTooLongError


def test_synthesize_invalid_emotion_raises(fake_model_manager):
    engine = TTSEngine(model_manager=fake_model_manager)
    with pytest.raises(InvalidEmotionError):
        engine.synthesize("Hello.", emotion="not_a_real_emotion")


def test_synthesize_stream_yields_progressively(fake_model_manager):
    engine = TTSEngine(model_manager=fake_model_manager)
    segments = list(engine.synthesize_stream("First. Second. Third."))
    assert len(segments) == 3
    assert segments[-1].is_final is True
    assert all(s.audio.size > 0 for s in segments)


def test_emotion_changes_output_duration(fake_model_manager):
    engine = TTSEngine(model_manager=fake_model_manager)
    neutral = engine.synthesize("This is a reasonably long test sentence.", emotion="neutral")
    excited = engine.synthesize("This is a reasonably long test sentence.", emotion="excited")
    # Excited speaks faster -> shorter audio duration for the same text.
    assert excited.audio_duration_s < neutral.audio_duration_s


def test_pause_tag_increases_total_duration(fake_model_manager):
    engine = TTSEngine(model_manager=fake_model_manager)
    baseline = engine.synthesize("Hello there. Goodbye.")
    with_pause = engine.synthesize("Hello there. [pause:1000ms] Goodbye.")
    assert with_pause.audio_duration_s > baseline.audio_duration_s
