"""Reading a photo of a paper card into a card for a person to check (task 0033).

Nothing is saved here: the card waits in the page that took the photo until a person
has checked it against the photo.
"""

import logging

from risk_assessment.domain.take5.scanned_card import ScannedCard, scanned_card
from risk_assessment.domain.take5.template import Take5Template
from risk_assessment.services.ports import CardReader

_logger: logging.Logger = logging.getLogger(__name__)

# The photo types the AI reads, and the most one photo may hold.
ACCEPTED_PHOTO_TYPES: frozenset[str] = frozenset(
    {"image/jpeg", "image/png", "image/webp", "image/gif"},
)
MAX_PHOTO_BYTES: int = 10 * 1024 * 1024
NO_AI_MESSAGE: str = "Scanning a paper card needs an AI, and none is set up."
WRONG_TYPE_MESSAGE: str = "Send a photo: a JPEG, PNG, WebP or GIF."
TOO_BIG_MESSAGE: str = "This photo is too big. Send one under 10 MB."
UNREADABLE_MESSAGE: str = (
    "This photo couldn't be read as a Take 5 card. "
    "Try a clearer photo of the whole card."
)


class ScanningUnavailableError(Exception):
    """No AI is set up, so no card can be read."""


class CardUnreadableError(Exception):
    """The AI failed, took too long, or sent back something that isn't a card."""


class CardScanner:
    """Reads photos of paper cards with an AI, for a person to check."""

    def __init__(self, reader: CardReader | None, template: Take5Template) -> None:
        """Choose the AI that reads, and the card the photos are of.

        Args:
            reader: The AI that reads photos, or None when none is set up.
            template: The card every photo is of.
        """
        self._reader: CardReader | None = reader
        self._template: Take5Template = template

    def read(self, photo: bytes, media_type: str) -> ScannedCard:
        """Read one photo into a card for a person to check.

        Args:
            photo: The photo's bytes.
            media_type: The photo's type, such as "image/jpeg".

        Returns:
            The card, kept to what the template allows.

        Raises:
            ScanningUnavailableError: No AI is set up.
            CardUnreadableError: The photo isn't an accepted type or is too big, or
                the AI failed, took too long, or its reply wasn't a card. The log
                names the kind of problem, never the reply.
        """
        if self._reader is None:
            raise ScanningUnavailableError(NO_AI_MESSAGE)
        if media_type not in ACCEPTED_PHOTO_TYPES:
            raise CardUnreadableError(WRONG_TYPE_MESSAGE)
        if len(photo) > MAX_PHOTO_BYTES:
            raise CardUnreadableError(TOO_BIG_MESSAGE)
        try:
            reply: str = self._reader.read(photo, media_type, self._template)
        except Exception as error:  # Any AI failure at all: the person retakes it.
            _logger.warning(
                "The AI could not read a card (%s).",
                type(error.__cause__ or error).__name__,
            )
            raise CardUnreadableError(UNREADABLE_MESSAGE) from error
        card: ScannedCard | None = scanned_card(reply, self._template)
        if card is None:
            _logger.warning("The AI's reading of a card wasn't the JSON asked for.")
            raise CardUnreadableError(UNREADABLE_MESSAGE)
        return card
