"""The Take 5 endpoints. They hold no rules; each hands back what the app gives it."""

from fastapi import APIRouter

from risk_assessment.api.schemas import TemplateResponse
from risk_assessment.domain.take5.template import BOOKLET_MATRIX

router: APIRouter = APIRouter(tags=["take5"])


@router.get("/api/take5/template")
def get_template() -> TemplateResponse:
    """Return the card a new Take 5 is filled in on.

    The front end draws what it is sent, so it never keeps its own copy of the card.
    """
    return TemplateResponse(matrix=BOOKLET_MATRIX)
