"""Thinking rules through checking, submission and a real storage round trip."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from httpx2 import Response

from risk_assessment.api.schemas import SubmissionRequest
from risk_assessment.domain.controls import ControlKind
from risk_assessment.domain.take5.draft import (
    ControlDraft,
    HazardDraft,
    RatingChoice,
    Take5Draft,
)
from risk_assessment.domain.take5.saved import SavedTake5
from risk_assessment.storage.sqlite import SqliteTake5Repository
from tests.samples import BARRICADE_DRAFT, sample_draft, sample_hazard_draft

QUESTION: str = (
    "Everything here relies on people getting it right. "
    "Could you remove, isolate or barricade it?"
)
REASON: str = "Live testing, so the panel can't be isolated"
ANSWER_PATH: str = "hazards.0.weak_controls_reason"


def _weak_hazard(reason: str = "") -> HazardDraft:
    """Make example 30, with a before score of 18 and only weak controls.

    Args:
        reason: The worker's answer to T3.

    Returns:
        A complete hazard except for its possibly missing answer.
    """
    return sample_hazard_draft(
        before=("Possible", "Major"),
        after=("Rare", "Major"),
        controls=(
            ControlDraft(description="Wear PPE", kind=ControlKind.PPE),
            ControlDraft(
                description="Ensure correct behaviour",
                kind=ControlKind.BEHAVIOUR,
            ),
        ),
    ).model_copy(update={"weak_controls_reason": reason})


@pytest.mark.parametrize("reason", ["", "  \n "])
def test_example_35_an_unanswered_question_blocks_submission(
    client: TestClient,
    repository: SqliteTake5Repository,
    reason: str,
) -> None:
    """Both check and save report the answer's path, without saving anything."""
    draft: Take5Draft = sample_draft(_weak_hazard(reason))
    request = SubmissionRequest(id=uuid4(), draft=draft)
    check: Response = client.post(
        "/api/take5s/check",
        json=draft.model_dump(mode="json"),
    )
    submitted: Response = client.post(
        "/api/take5s",
        json=request.model_dump(mode="json"),
    )

    assert check.status_code == 200
    assert check.json()["thinking_questions"] == [
        {"path": ANSWER_PATH, "message": QUESTION},
    ]
    assert check.json()["can_submit"] is False
    assert submitted.status_code == 422
    assert submitted.json() == {
        "detail": "Fill in the highlighted fields before you submit.",
        "errors": [{"path": ANSWER_PATH, "message": "Fill in this field."}],
    }
    assert repository.get(request.id) is None


def test_example_36_the_answer_is_saved_without_changing_the_verdict(
    client: TestClient,
    repository: SqliteTake5Repository,
) -> None:
    """An answered question still applies; its text survives SQLite and GET."""
    request = SubmissionRequest(id=uuid4(), draft=sample_draft(_weak_hazard(REASON)))
    check: Response = client.post(
        "/api/take5s/check",
        json=request.draft.model_dump(mode="json"),
    )
    response: Response = client.post(
        "/api/take5s",
        json=request.model_dump(mode="json"),
    )

    assert check.json()["can_submit"] is True
    assert check.json()["thinking_questions"] == [
        {"path": ANSWER_PATH, "message": QUESTION},
    ]
    assert response.status_code == 200
    saved: SavedTake5 | None = repository.get(request.id)
    assert saved is not None
    assert saved.hazards[0].weak_controls_reason == REASON
    assert saved.verdict.can_start
    assert saved.verdict.reasons == ()
    assert client.get(f"/api/take5s/{request.id}").json() == response.json()
    assert (
        client.post("/api/take5s", json=request.model_dump(mode="json")).json()
        == response.json()
    )


def test_a_different_answer_cannot_replace_a_saved_answer(client: TestClient) -> None:
    """Retrying with changed wording gives 409 and leaves the first answer alone."""
    request = SubmissionRequest(id=uuid4(), draft=sample_draft(_weak_hazard(REASON)))
    client.post("/api/take5s", json=request.model_dump(mode="json"))
    changed = SubmissionRequest(
        id=request.id,
        draft=sample_draft(_weak_hazard("Another reason")),
    )
    response: Response = client.post(
        "/api/take5s",
        json=changed.model_dump(mode="json"),
    )
    assert response.status_code == 409
    assert (
        client.get(f"/api/take5s/{request.id}").json()["take5"]["hazards"][0][
            "weak_controls_reason"
        ]
        == REASON
    )


@pytest.mark.parametrize(
    ("draft", "path", "message"),
    [
        (
            sample_draft().model_copy(update={"job": "Change tyre"}),
            "job",
            "Describe the job in at least four words.",
        ),
        (
            sample_draft(
                sample_hazard_draft(
                    controls=(
                        ControlDraft(description="Be careful.", kind=ControlKind.PPE),
                    ),
                ),
            ),
            "hazards.0.controls.0.description",
            "Say what you'll actually do.",
        ),
    ],
)
def test_wording_errors_are_inline_errors_on_check_and_save(
    client: TestClient,
    draft: Take5Draft,
    path: str,
    message: str,
) -> None:
    """T2 and T4 cannot be bypassed by posting straight to save."""
    request = SubmissionRequest(id=uuid4(), draft=draft)
    check: Response = client.post(
        "/api/take5s/check",
        json=draft.model_dump(mode="json"),
    )
    save: Response = client.post("/api/take5s", json=request.model_dump(mode="json"))
    assert check.json()["errors"] == [{"path": path, "message": message}]
    assert check.json()["can_submit"] is False
    assert save.status_code == 422
    assert save.json()["errors"] == check.json()["errors"]


@pytest.mark.parametrize("reason", ["", REASON])
def test_a_strong_control_removes_the_question_and_the_reason_is_not_rated(
    client: TestClient,
    reason: str,
) -> None:
    """A strong control is the alternative to answering.

    The phone's draft still holds what was written, but the rated hazard doesn't, so a
    saved Take 5 never explains why a strong control it lists wasn't possible.
    """
    hazard: HazardDraft = _weak_hazard(reason)
    hazard = hazard.model_copy(update={"controls": (*hazard.controls, BARRICADE_DRAFT)})
    response: Response = client.post(
        "/api/take5s/check",
        json=sample_draft(hazard).model_dump(mode="json"),
    )
    assert response.json()["thinking_questions"] == []
    assert response.json()["can_submit"] is True
    assert response.json()["assessment"]["hazards"][0]["weak_controls_reason"] == ""


def test_the_question_appears_before_the_after_rating_is_picked(
    client: TestClient,
) -> None:
    """T3 can be shown on the controls page, before the worker rates it again."""
    hazard: HazardDraft = _weak_hazard().model_copy(update={"after": RatingChoice()})
    response: Response = client.post(
        "/api/take5s/check",
        json=sample_draft(hazard).model_dump(mode="json"),
    )
    assert response.json()["thinking_questions"] == [
        {"path": ANSWER_PATH, "message": QUESTION},
    ]
