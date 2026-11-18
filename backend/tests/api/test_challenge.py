"""Integration tests for the challenge question through the API (spec C1 to C6, F6)."""

from typing import Any
from uuid import uuid4

from fastapi.testclient import TestClient
from httpx2 import Response

from risk_assessment.api.app import create_app
from risk_assessment.domain.take5.challenge import AiQuestion
from risk_assessment.storage.sqlite import SqliteTake5Repository
from tests.api.take5_requests import answer, finish, submit
from tests.samples import SAMPLE_ANSWER, sample_draft

FALLBACK_ABOUT_THE_WHEEL: str = (
    "What is the one thing that has to go right so that 'Moving wheel' doesn't hurt "
    "anyone, and how will you check it before you start?"
)


class FailingAsker:
    """A stand-in AI that always fails, as one with no signal would."""

    def ask(self, take5_text: str) -> AiQuestion:
        """Fail whatever is asked.

        Args:
            take5_text: The Take 5, as the service wrote it out.

        Raises:
            ConnectionError: Always.
        """
        raise ConnectionError("Example provider could not be reached.")


def test_a_submitted_take5_comes_back_unfinished_with_its_question(
    client: TestClient,
) -> None:
    """No verdict yet, and with no AI set up the fixed question is asked (C3, C6)."""
    submitted: dict[str, Any] = submit(client, sample_draft())

    assert submitted["take5"]["verdict"] is None
    assert submitted["take5"]["finished_at"] is None
    assert submitted["take5"]["challenge"] == {
        "question": FALLBACK_ABOUT_THE_WHEEL,
        "asked_by": "fallback",
        "model": None,
        "instructions_version": None,
        "answer": None,
    }
    assert submitted["offers_fix"] is False


def test_an_ai_error_is_never_sent_to_the_worker(
    repository: SqliteTake5Repository,
) -> None:
    """The AI fails; the reply is still a 200 with the fixed question (F6)."""
    client = TestClient(create_app(repository, challenge_asker=FailingAsker()))

    submitted: dict[str, Any] = submit(client, sample_draft())

    assert submitted["take5"]["challenge"]["question"] == FALLBACK_ABOUT_THE_WHEEL


def test_opening_an_unfinished_take5_shows_the_same_question(
    client: TestClient,
) -> None:
    """Example 54 through the API: the question is kept, not asked again (C6)."""
    submitted: dict[str, Any] = submit(client, sample_draft())

    reopened: Response = client.get(f"/api/take5s/{submitted['take5']['id']}")

    assert reopened.json() == submitted


def test_answering_finishes_the_take5_with_its_answer_and_verdict(
    client: TestClient,
) -> None:
    """Example 52 through the API: the reply is the finished Take 5 (C4, C5)."""
    take5_id: str = submit(client, sample_draft())["take5"]["id"]

    response: Response = answer(client, take5_id, f" {SAMPLE_ANSWER}  ")

    assert response.status_code == 200
    finished: dict[str, Any] = response.json()["take5"]
    assert finished["verdict"] == {"can_start": True, "reasons": []}
    assert finished["finished_at"] is not None
    assert finished["challenge"]["answer"] == SAMPLE_ANSWER
    assert client.get(f"/api/take5s/{take5_id}").json() == response.json()


def test_a_short_answer_is_a_422_beside_the_answer(client: TestClient) -> None:
    """Example 51 through the API: the error is named on the `answer` field (C4)."""
    take5_id: str = submit(client, sample_draft())["take5"]["id"]

    response: Response = answer(client, take5_id, "Chocked both sides")

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Answer the question before you finish.",
        "errors": [
            {
                "path": "answer",
                "message": (
                    "Answer in at least four words: say what you'll check or do."
                ),
            },
        ],
    }
    assert client.get(f"/api/take5s/{take5_id}").json()["take5"]["verdict"] is None


def test_a_second_answer_is_a_409_and_the_first_is_kept(client: TestClient) -> None:
    """Example 55 through the API (C6)."""
    finished: dict[str, Any] = finish(client, sample_draft())
    take5_id: str = finished["take5"]["id"]

    response: Response = answer(client, take5_id, "Someone else checked the chocks")

    assert response.status_code == 409
    assert response.json() == {
        "detail": "This Take 5 is already finished, so it can't be answered again.",
    }
    assert client.get(f"/api/take5s/{take5_id}").json() == finished


def test_answering_an_unknown_take5_is_a_404(client: TestClient) -> None:
    """There is nothing to answer."""
    response: Response = answer(client, str(uuid4()))

    assert response.status_code == 404
    assert response.json() == {"detail": "This Take 5 could not be found."}
