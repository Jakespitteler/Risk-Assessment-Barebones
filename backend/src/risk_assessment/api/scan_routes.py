"""The scanning endpoint. It turns HTTP into a service call and holds no rules."""

from typing import Annotated, Any

from fastapi import APIRouter, File, UploadFile

from risk_assessment.api.schemas import ErrorMessage, FormErrors, ScannedCardResponse
from risk_assessment.domain.take5.scanned_card import ScannedCard
from risk_assessment.services.card_scanning import MAX_PHOTO_BYTES, CardScanner

_RESPONSES: dict[int | str, dict[str, Any]] = {
    422: {
        "model": FormErrors,
        "description": "Not an accepted photo, too big, or not readable as a card",
    },
    503: {"model": ErrorMessage, "description": "No AI is set up to read cards"},
}


def create_scan_router(scanner: CardScanner) -> APIRouter:
    """Bind the scanning endpoint to the scanner that the composition root built.

    Args:
        scanner: The scanner the endpoint calls.

    Returns:
        The router with the scanning endpoint.
    """
    router = APIRouter(tags=["scanning"])

    @router.post("/api/scans", responses=_RESPONSES)
    def read_card(photo: Annotated[UploadFile, File()]) -> ScannedCardResponse:
        """Read a photo of a paper card into a card to check; nothing is saved.

        Args:
            photo: The photo of one paper card.
        """
        # One byte over the limit is enough to know it is too big.
        photo_bytes: bytes = photo.file.read(MAX_PHOTO_BYTES + 1)
        # "IMAGE/JPEG" or "image/jpeg; charset=binary" is still a JPEG.
        media_type: str = (photo.content_type or "").split(";")[0].strip().lower()
        card: ScannedCard = scanner.read(photo_bytes, media_type)
        return ScannedCardResponse(
            draft=card.draft,
            filled_in_at=card.filled_in_at,
            unreadable=card.unreadable,
        )

    return router
