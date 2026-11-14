"""Shared wording boundaries, including the phrases that later rules reuse."""

import pytest

from risk_assessment.domain.wording import is_vague, word_count


@pytest.mark.parametrize(
    "phrase",
    [
        "be careful",
        "take care",
        "take 5",
        "watch out",
        "stay alert",
        "pay attention",
        "use common sense",
        "be aware",
    ],
)
def test_every_vague_phrase_ignores_case_punctuation_and_spaces(phrase: str) -> None:
    """Every phrase in T2 is recognised, with no substring matching."""
    assert is_vague(f"  {phrase.upper().replace(' ', '  ')}!  ")
    assert not is_vague(f"{phrase} of the moving wheel")


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("", 0),
        (" \n\t ", 0),
        ("... !", 0),
        ("Change\n tyre\t on  LV12", 4),
        ("Don't re-enter", 2),
    ],
)
def test_words_need_letters_or_digits(text: str, expected: int) -> None:
    """Whitespace separates words; punctuation alone does not pad an answer."""
    assert word_count(text) == expected
