"""The shapes of the API's requests and responses."""

from uuid import UUID

from pydantic import BaseModel

from risk_assessment.domain.controls import ControlKind
from risk_assessment.domain.risk import RiskMatrix, RiskRating
from risk_assessment.domain.take5.draft import Take5Draft
from risk_assessment.domain.take5.saved import SavedTake5


class TemplateResponse(BaseModel):
    """The card and control choices; the phone keeps no copy of these rules."""

    name: str
    matrix: RiskMatrix
    control_kinds: tuple[ControlKind, ...]
    likelihood_guidance: tuple[tuple[str, str], ...]
    consequence_guidance: tuple[tuple[str, str], ...]
    control_guidance: str


class SubmissionRequest(BaseModel):
    """A stable submission ID makes retries return the first saved result."""

    id: UUID
    draft: Take5Draft


class Take5Response(BaseModel):
    """The saved document, with its overall score and band derived by the domain."""

    take5: SavedTake5
    rating: RiskRating
