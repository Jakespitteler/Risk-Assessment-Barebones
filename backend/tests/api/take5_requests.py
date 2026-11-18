"""Requests that many API tests send: submit a Take 5, and answer its question."""

from typing import Any
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from httpx2 import Response

from risk_assessment.api.schemas import SubmissionRequest
from risk_assessment.domain.take5.draft import Take5Draft
from tests.samples import SAMPLE_ANSWER


def submit(
    client: TestClient,
    draft: Take5Draft,
    take5_id: UUID | None = None,
) -> dict[str, Any]:
    """Save a Take 5 through the API, which leaves it unfinished with its question.

    Args:
        client: The test client.
        draft: The worker's answers.
        take5_id: The submission ID, or None for a new one.

    Returns:
        The reply, as the API sent it.
    """
    request = SubmissionRequest(id=take5_id or uuid4(), draft=draft)
    response: Response = client.post(
        "/api/take5s",
        json=request.model_dump(mode="json"),
    )
    assert response.status_code == 200
    return response.json()


def answer(
    client: TestClient,
    take5_id: str,
    worker_answer: str = SAMPLE_ANSWER,
) -> Response:
    """Answer a saved Take 5's question through the API.

    Args:
        client: The test client.
        take5_id: The Take 5's ID.
        worker_answer: What the worker wrote.

    Returns:
        The API's response.
    """
    return client.post(
        f"/api/take5s/{take5_id}/answer",
        json={"answer": worker_answer},
    )


def finish(client: TestClient, draft: Take5Draft) -> dict[str, Any]:
    """Save a Take 5 and answer its question, so it has its verdict.

    Args:
        client: The test client.
        draft: The worker's answers.

    Returns:
        The finished Take 5's reply, as the API sent it.
    """
    take5_id: str = submit(client, draft)["take5"]["id"]
    response: Response = answer(client, take5_id)
    assert response.status_code == 200
    return response.json()
