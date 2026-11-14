"""Shared wording checks for descriptions and answers."""

VAGUE_PHRASES: frozenset[str] = frozenset(
    {
        "be careful",
        "take care",
        "take 5",
        "watch out",
        "stay alert",
        "pay attention",
        "use common sense",
        "be aware",
    },
)


def is_vague(text: str) -> bool:
    """Check whether the whole answer is one of the vague phrases.

    Args:
        text: The worker's wording, including any capitals or punctuation.

    Returns:
        True for an exact phrase after ignoring case, punctuation and extra spaces.
    """
    letters: str = "".join(
        character if character.isalnum() else " " for character in text.casefold()
    )
    normalised: str = " ".join(letters.split())
    return normalised in VAGUE_PHRASES


def word_count(text: str) -> int:
    """Count words separated by whitespace, ignoring punctuation-only tokens.

    Args:
        text: The worker's wording.

    Returns:
        The number of tokens containing a letter or digit. A hyphenated word or a
        contraction counts once.
    """
    return sum(any(character.isalnum() for character in word) for word in text.split())
