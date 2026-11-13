"""Tests for the Take 5 endpoints, through FastAPI's test client."""

from fastapi.testclient import TestClient

from risk_assessment.api.app import create_app


def test_the_template_sends_the_booklet_matrix() -> None:
    """The front end gets the whole matrix, so it never needs its own copy."""
    client = TestClient(create_app())

    response = client.get("/api/take5/template")

    assert response.status_code == 200
    matrix = response.json()["matrix"]
    assert matrix["likelihoods"][-1] == "Rare"
    assert matrix["consequences"][0] == "Low"
    assert matrix["cells"][-1][0] == {"score": 1, "band": "Low"}
    assert matrix["jha_threshold"] == 11
