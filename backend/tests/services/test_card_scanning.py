"""Tests for reading a photo into a card to check, saving nothing (task 0033)."""

import json
import logging

import pytest

from risk_assessment.domain.take5.scanned_card import ScannedCard
from risk_assessment.domain.take5.template import BOOKLET_TEMPLATE, Take5Template
from risk_assessment.services.card_scanning import (
    EMPTY_MESSAGE,
    MAX_PHOTO_BYTES,
    TOO_BIG_MESSAGE,
    UNREADABLE_MESSAGE,
    WRONG_TYPE_MESSAGE,
    CardScanner,
    CardUnreadableError,
    ScanningUnavailableError,
)

CARD_REPLY: str = json.dumps(
    {"worker_name": "Sam Example", "job": "Change the front left tyre on LV12"},
)


class StandInReader:
    """A stand-in for the AI that reads cards: replies as set, or fails."""

    def __init__(
        self,
        reply: str = CARD_REPLY,
        failure: Exception | None = None,
    ) -> None:
        """Set what it does when asked.

        Args:
            reply: What it sends back.
            failure: An error to raise instead, or None.
        """
        self._reply: str = reply
        self._failure: Exception | None = failure

    def read(self, photo: bytes, media_type: str, template: Take5Template) -> str:
        """Reply as set, or fail.

        Args:
            photo: Unused.
            media_type: Unused.
            template: Unused.

        Returns:
            The set reply.

        Raises:
            Exception: The set failure, if any.
        """
        if self._failure is not None:
            raise self._failure
        return self._reply


def test_a_photo_is_read_into_a_card_to_check() -> None:
    """The card comes back for a person to check; nothing is saved."""
    card: ScannedCard = CardScanner(StandInReader(), BOOKLET_TEMPLATE).read(
        b"photo",
        "image/jpeg",
    )

    assert card.draft.job == "Change the front left tyre on LV12"


def test_with_no_ai_scanning_says_it_needs_one() -> None:
    """Scanning is an AI-only feature (spec D67)."""
    with pytest.raises(ScanningUnavailableError):
        CardScanner(None, BOOKLET_TEMPLATE).read(b"photo", "image/jpeg")


@pytest.mark.parametrize(
    ("photo", "media_type", "message"),
    [
        (b"%PDF", "application/pdf", WRONG_TYPE_MESSAGE),
        (b"x" * (MAX_PHOTO_BYTES + 1), "image/jpeg", TOO_BIG_MESSAGE),
        (b"", "image/jpeg", EMPTY_MESSAGE),
    ],
    ids=["not_a_photo", "too_big", "empty"],
)
def test_a_wrong_type_or_too_big_photo_is_refused_before_the_ai(
    photo: bytes,
    media_type: str,
    message: str,
) -> None:
    """Nothing is sent to the AI for a file it can't read."""
    reader = StandInReader(failure=AssertionError("the AI must not be asked"))

    with pytest.raises(CardUnreadableError, match=message):
        CardScanner(reader, BOOKLET_TEMPLATE).read(photo, media_type)


def test_an_ai_failure_says_to_retake_and_logs_one_line_without_the_name(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The person sees a plain message; the log names the kind, not the card."""
    reader = StandInReader(failure=ConnectionError("Sam Example's card"))

    with (
        caplog.at_level(logging.WARNING, logger="risk_assessment"),
        pytest.raises(CardUnreadableError, match="Try a clearer photo"),
    ):
        CardScanner(reader, BOOKLET_TEMPLATE).read(b"photo", "image/jpeg")

    assert "ConnectionError" in caplog.text
    assert "Sam Example" not in caplog.text


def test_a_reply_that_is_not_a_card_says_to_retake() -> None:
    """An apology or a refusal is not a card."""
    reader = StandInReader(reply="Sorry, I can't read handwriting.")

    with pytest.raises(CardUnreadableError) as refusal:
        CardScanner(reader, BOOKLET_TEMPLATE).read(b"photo", "image/jpeg")

    assert str(refusal.value) == UNREADABLE_MESSAGE
