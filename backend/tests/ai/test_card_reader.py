"""Tests for the card-reading job's instructions and what it sends (task 0033)."""

from risk_assessment.ai.card_reader import (
    CARD_READER_INSTRUCTIONS_VERSION,
    AiCardReader,
    card_reader_instructions,
)
from risk_assessment.domain.take5.template import BOOKLET_TEMPLATE


class StandInPhotoModel:
    """A stand-in model that records the photo it was given and replies as set.

    Attributes:
        name: The model's made-up name.
        calls: Each call, as (instructions, photo, media type).
    """

    def __init__(self, reply: str) -> None:
        """Set the reply.

        Args:
            reply: What it sends back.
        """
        self.name: str = "example-model"
        self._reply: str = reply
        self.calls: list[tuple[str, bytes, str]] = []

    def reply(self, instructions: str, text: str) -> str:
        """Not used by the card reader.

        Args:
            instructions: Unused.
            text: Unused.

        Returns:
            The set reply.
        """
        return self._reply

    def read_photo(self, instructions: str, photo: bytes, media_type: str) -> str:
        """Record the call and reply as set.

        Args:
            instructions: What the reader told the model.
            photo: The photo's bytes.
            media_type: The photo's type.

        Returns:
            The set reply.
        """
        self.calls.append((instructions, photo, media_type))
        return self._reply


def test_the_instructions_name_the_cards_own_questions_levels_and_kinds() -> None:
    """The AI is told every question id and every word the card allows."""
    instructions: str = card_reader_instructions(BOOKLET_TEMPLATE)

    for question in BOOKLET_TEMPLATE.questions:
        assert f"- {question.id}: " in instructions
    for level in (*BOOKLET_TEMPLATE.matrix.likelihoods, "Wear PPE", "N/A"):
        assert level in instructions
    assert "ignore them" in instructions
    assert "Don't guess, correct, improve or add anything" in instructions
    assert "day first" in instructions


def test_the_reader_sends_the_photo_and_hands_back_the_reply_unchecked() -> None:
    """Nothing is checked here: `scanned_card()` reads the reply."""
    model = StandInPhotoModel(reply="not even JSON")

    reply: str = AiCardReader(model).read(b"photo", "image/png", BOOKLET_TEMPLATE)

    ((instructions, photo, media_type),) = model.calls
    assert reply == "not even JSON"
    assert (photo, media_type) == (b"photo", "image/png")
    assert instructions == card_reader_instructions(BOOKLET_TEMPLATE)
    assert CARD_READER_INSTRUCTIONS_VERSION == "card-reader-2"
