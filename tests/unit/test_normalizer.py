from text.normalizer import normalize


def test_expands_common_abbreviations():
    assert "Doctor Smith" in normalize("Dr. Smith")


def test_expands_currency():
    result = normalize("It costs $12.50 today.")
    assert "$" not in result
    assert "twelve dollars" in result
    assert "fifty cents" in result


def test_expands_percentage():
    result = normalize("Sales grew 20%.")
    assert "%" not in result
    assert "twenty percent" in result


def test_expands_plain_numbers():
    result = normalize("I have 42 apples.")
    assert "forty-two" in result


def test_preserves_inline_pause_tags():
    result = normalize("Wait for it... [pause:500ms] surprise!")
    assert "[pause:500ms]" in result


def test_collapses_excess_whitespace_and_newlines():
    result = normalize("Hello   world\n\n\n\nBye")
    assert "   " not in result
    assert "\n\n\n" not in result


def test_empty_input_returns_empty():
    assert normalize("") == ""
