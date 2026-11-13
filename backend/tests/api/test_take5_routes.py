"""Tests for the Take 5 endpoints, through FastAPI's test client."""

from fastapi.testclient import TestClient
from httpx2 import Response

from risk_assessment.api.app import create_app
from risk_assessment.api.schemas import TemplateResponse
from risk_assessment.domain.risk import RiskCell, RiskMatrix


def test_the_template_sends_the_booklet_matrix() -> None:
    """The front end gets the whole matrix, so it never needs its own copy."""
    client = TestClient(create_app())

    response: Response = client.get("/api/take5/template")

    assert response.status_code == 200
    matrix: RiskMatrix = TemplateResponse.model_validate(response.json()).matrix
    assert matrix.likelihoods[-1] == "Rare"
    assert matrix.consequences[0] == "Low"
    assert matrix.cells[-1][0] == RiskCell(score=1, band="Low")
    assert matrix.jha_threshold == 11
