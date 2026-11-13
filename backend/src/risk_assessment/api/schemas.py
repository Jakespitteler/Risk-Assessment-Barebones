"""The shapes of the API's requests and responses."""

from pydantic import BaseModel

from risk_assessment.domain.risk import RiskMatrix


class TemplateResponse(BaseModel):
    """What `GET /api/take5/template` returns.

    For now this is only the risk matrix. Task 0004 adds the card's questions and the
    kinds of control.
    """

    matrix: RiskMatrix
