"""Tests for what each Take 5 endpoint sends, including its declared error replies."""

from typing import Any

import pytest
from fastapi.testclient import TestClient
from httpx2 import Response

from risk_assessment.api.app import create_app
from risk_assessment.api.schemas import TemplateResponse
from risk_assessment.domain.controls import ControlKind
from risk_assessment.domain.questions import Answer
from risk_assessment.domain.risk import RiskCell, RiskMatrix
from risk_assessment.domain.take5.template import BOOKLET_TEMPLATE, LevelGuidance


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


def test_the_template_sends_the_templates_own_guidance_and_every_control_kind() -> None:
    """The guidance comes from the template, so a saved copy keeps it too."""
    client = TestClient(create_app())

    template: TemplateResponse = TemplateResponse.model_validate(
        client.get("/api/take5/template").json(),
    )

    assert template.likelihood_guidance == BOOKLET_TEMPLATE.likelihood_guidance
    assert template.consequence_guidance == BOOKLET_TEMPLATE.consequence_guidance
    assert template.control_guidance == BOOKLET_TEMPLATE.control_guidance
    assert template.likelihood_guidance[0] == LevelGuidance(
        level="Almost Certain",
        meaning="Expected to happen: once a week.",
    )
    assert template.control_kinds == tuple(ControlKind)


def test_the_template_sends_its_questions_and_the_answers_they_can_have() -> None:
    """The phone draws whatever questions the template holds, in the card's order."""
    client = TestClient(create_app())

    template: TemplateResponse = TemplateResponse.model_validate(
        client.get("/api/take5/template").json(),
    )

    assert template.questions == BOOKLET_TEMPLATE.questions
    assert template.answer_choices == (Answer.YES, Answer.NO, Answer.NOT_APPLICABLE)


def _responses(path: str, method: str) -> dict[str, Any]:
    """Get the replies the API description declares for one endpoint.

    Args:
        path: The endpoint's path.
        method: The HTTP method, in lower case.

    Returns:
        The declared replies, by status code.
    """
    description: dict[str, Any] = create_app().openapi()
    return description["paths"][path][method]["responses"]


@pytest.mark.parametrize(
    ("path", "method", "errors"),
    [
        ("/api/take5s/check", "post", {"422": "FormErrors"}),
        ("/api/take5s", "post", {"422": "FormErrors", "409": "ErrorMessage"}),
        (
            "/api/take5s/{take5_id}",
            "get",
            {"422": "FormErrors", "404": "ErrorMessage"},
        ),
    ],
)
def test_every_error_reply_is_declared_with_one_shape(
    path: str,
    method: str,
    errors: dict[str, str],
) -> None:
    """The front end's generated types know every error an endpoint can send."""
    responses: dict[str, Any] = _responses(path, method)

    declared: dict[str, str] = {
        status: reply["content"]["application/json"]["schema"]["$ref"].split("/")[-1]
        for status, reply in responses.items()
        if status != "200"
    }

    assert declared == errors
