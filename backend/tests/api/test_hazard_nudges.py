"""Integration tests for judging vague hazards through the API (spec T6)."""

from typing import Any

from fastapi.testclient import TestClient
from httpx2 import Response

from risk_assessment.api.app import create_app
from risk_assessment.domain.questions import Answer
from risk_assessment.domain.take5.draft import HazardDraft, Take5Draft
from risk_assessment.domain.take5.hazard_nudges import HAZARD_AI_NOTICE
from risk_assessment.storage.sqlite import SqliteTake5Repository
from tests.samples import sample_answers, sample_draft, sample_hazard_draft


class FailingJudge:
    """A stand-in AI that always fails, as one with no signal would."""

    def judge(self, hazard_text: str) -> str:
        """Fail whatever is asked.

        Args:
            hazard_text: The hazard, as the service wrote it out.

        Raises:
            ConnectionError: Always.
        """
        raise ConnectionError("Example provider could not be reached.")


class SpecificJudge:
    """A stand-in AI that calls every hazard specific."""

    def judge(self, hazard_text: str) -> str:
        """Call the hazard specific.

        Args:
            hazard_text: The hazard, as the service wrote it out.

        Returns:
            "specific".
        """
        return "specific"


def _crusher_dust_on_vehicles() -> Take5Draft:
    """Make a draft with a two-word hazard linked to the vehicles question's Yes.

    Returns:
        The draft.
    """
    hazard: HazardDraft = sample_hazard_draft().model_copy(
        update={"description": "Crusher dust", "covers": ("vehicles",)},
    )
    return sample_draft(hazard).model_copy(
        update={"answers": sample_answers(vehicles=Answer.YES)},
    )


def _nudges(client: TestClient, draft: Take5Draft) -> list[dict[str, str]]:
    """Ask the API for a draft's nudges.

    Args:
        client: The test client.
        draft: The draft to send.

    Returns:
        The nudges, as JSON.
    """
    response: Response = client.post(
        "/api/take5s/nudges",
        json=draft.model_dump(mode="json"),
    )
    assert response.status_code == 200
    return response.json()


def test_the_ais_verdict_decides_the_nudges(
    repository: SqliteTake5Repository,
) -> None:
    """Example 77 through the API: two words, but the AI says specific."""
    client = TestClient(create_app(repository, hazard_judge=SpecificJudge()))

    assert _nudges(client, _crusher_dust_on_vehicles()) == []


def test_an_ai_error_is_never_sent_to_the_worker(
    repository: SqliteTake5Repository,
) -> None:
    """The AI fails; the reply is still a 200, with the word rule's nudge (T6)."""
    client = TestClient(create_app(repository, hazard_judge=FailingJudge()))

    nudges: list[dict[str, str]] = _nudges(client, _crusher_dust_on_vehicles())

    assert [nudge["question_id"] for nudge in nudges] == ["vehicles"]


def test_with_no_ai_the_template_has_no_hazard_notice(client: TestClient) -> None:
    """Nothing is sent to an AI, so the hazard check page says nothing (D63)."""
    template: dict[str, Any] = client.get("/api/take5/template").json()

    assert template["hazard_ai_notice"] is None


def test_with_an_ai_the_template_says_hazards_go_to_it(
    repository: SqliteTake5Repository,
) -> None:
    """The notice says linked hazards go to an AI, and that the name doesn't (D63)."""
    client = TestClient(create_app(repository, hazard_judge=FailingJudge()))

    template: dict[str, Any] = client.get("/api/take5/template").json()

    assert template["hazard_ai_notice"] == HAZARD_AI_NOTICE
    assert "Your name isn't sent" in HAZARD_AI_NOTICE
