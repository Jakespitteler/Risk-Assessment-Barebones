"""Integration tests for checking, submitting, retrying and reopening a Take 5."""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from httpx2 import Response

from risk_assessment.api.app import create_app
from risk_assessment.api.schemas import SubmissionRequest, Take5Response
from risk_assessment.domain.controls import ControlKind
from risk_assessment.domain.questions import Answer
from risk_assessment.domain.take5.draft import (
    ControlDraft,
    HazardDraft,
    RatingChoice,
    Take5Draft,
)
from risk_assessment.domain.take5.template import BOOKLET_TEMPLATE
from risk_assessment.storage.sqlite import SqliteTake5Repository
from tests.api.take5_requests import answer, finish
from tests.samples import sample_answers, sample_draft, sample_uncontrolled_draft


def test_submit_and_reopen_preserve_the_original_document(tmp_path: Path) -> None:
    """A fresh repository instance retrieves the verdict, template and ratings."""
    database: Path = tmp_path / "take5.sqlite3"
    client = TestClient(create_app(SqliteTake5Repository(database)))
    request = SubmissionRequest(id=uuid4(), draft=sample_draft())
    response: Response = client.post(
        "/api/take5s",
        json=request.model_dump(mode="json"),
    )
    assert response.status_code == 200
    finished: Response = answer(client, str(request.id))
    saved: Take5Response = Take5Response.model_validate(finished.json())
    assert saved.take5.verdict is not None and saved.take5.verdict.can_start
    assert saved.rating.score == 5 and saved.rating.band == "Low"
    assert saved.take5.template.matrix.jha_threshold == 11
    reopened: Response = TestClient(create_app(SqliteTake5Repository(database))).get(
        f"/api/take5s/{request.id}",
    )
    assert reopened.json() == finished.json()
    assert client.post(f"/api/take5s/{request.id}", json={}).status_code == 405


def test_retries_return_one_document_and_different_input_cannot_replace_it(
    client: TestClient,
) -> None:
    """A stable ID covers repeated clicks and a retry after a lost response."""
    request = SubmissionRequest(id=uuid4(), draft=sample_draft())
    first: Response = client.post("/api/take5s", json=request.model_dump(mode="json"))
    retry: Response = client.post("/api/take5s", json=request.model_dump(mode="json"))
    assert retry.json() == first.json()
    changed: SubmissionRequest = request.model_copy(
        update={
            "draft": request.draft.model_copy(
                update={"job": "Another example tyre job"},
            ),
        },
    )
    assert (
        client.post("/api/take5s", json=changed.model_dump(mode="json")).status_code
        == 409
    )
    assert client.get(f"/api/take5s/{request.id}").json() == first.json()


def test_check_returns_all_missing_fields_without_creating_storage(
    tmp_path: Path,
) -> None:
    """Checking never writes data; errors belong beside their named fields."""
    database: Path = tmp_path / "take5.sqlite3"
    client = TestClient(create_app(SqliteTake5Repository(database)))
    response: Response = client.post("/api/take5s/check", json={})
    assert response.status_code == 200
    paths: set[str] = {error["path"] for error in response.json()["errors"]}
    assert paths == {
        "worker_name",
        "job",
        "location",
        "hazards",
        *(f"answers.{question.id}" for question in BOOKLET_TEMPLATE.questions),
    }
    assert not response.json()["can_submit"]
    assert not database.exists()


@pytest.mark.parametrize(
    "path",
    ["description", "before", "after", "control_description", "control_kind"],
)
def test_each_incomplete_hazard_field_blocks_submission(
    client: TestClient,
    repository: SqliteTake5Repository,
    path: str,
) -> None:
    """The API reports the exact missing field and refuses to save the draft."""
    draft: Take5Draft = sample_draft()
    hazard: HazardDraft = draft.hazards[0]
    if path == "description":
        hazard = hazard.model_copy(update={"description": "  "})
    elif path in ("before", "after"):
        hazard = hazard.model_copy(update={path: RatingChoice(likelihood="Possible")})
    else:
        control = ControlDraft(
            description="" if path == "control_description" else "Example control",
            kind=None if path == "control_kind" else ControlKind.BARRICADE,
        )
        hazard = hazard.model_copy(update={"controls": (control,)})
    draft = draft.model_copy(update={"hazards": (hazard,)})
    submission_id: UUID = uuid4()
    response: Response = client.post(
        "/api/take5s",
        json=SubmissionRequest(id=submission_id, draft=draft).model_dump(mode="json"),
    )
    assert response.status_code == 422
    assert response.json()["errors"][0]["path"].startswith("hazards.0.")
    assert repository.get(submission_id) is None


def test_without_controls_after_is_derived_and_the_verdict_stops_the_job(
    client: TestClient,
) -> None:
    """A hazard without controls can be submitted but must stop the job."""
    saved: Take5Response = Take5Response.model_validate(
        finish(client, sample_uncontrolled_draft()),
    )
    assert saved.take5.verdict is not None and not saved.take5.verdict.can_start
    assert saved.take5.hazards[0].after == saved.take5.hazards[0].before
    assert saved.rating.score == 8


def test_higher_after_risk_and_unknown_scale_choices_are_field_errors(
    client: TestClient,
) -> None:
    """A client cannot invent ratings or increase risk through controls."""
    draft: Take5Draft = sample_draft()
    for after in (
        RatingChoice(likelihood="Almost Certain", consequence="Critical"),
        RatingChoice(likelihood="Invented", consequence="Minor"),
    ):
        hazard: HazardDraft = draft.hazards[0].model_copy(update={"after": after})
        response: Response = client.post(
            "/api/take5s/check",
            json=draft.model_copy(update={"hazards": (hazard,)}).model_dump(
                mode="json",
            ),
        )
        assert not response.json()["can_submit"]
        assert response.json()["errors"][0]["path"].startswith("hazards.0.after")


@pytest.mark.parametrize("field", ["worker_name", "job", "location"])
def test_a_blank_name_job_or_location_cannot_be_submitted(
    client: TestClient,
    repository: SqliteTake5Repository,
    field: str,
) -> None:
    """Each blank field comes back as a 422 naming that field, and nothing is saved."""
    request = SubmissionRequest(
        id=uuid4(),
        draft=sample_draft().model_copy(update={field: " "}),
    )

    response: Response = client.post(
        "/api/take5s",
        json=request.model_dump(mode="json"),
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Fill in the highlighted fields before you submit.",
        "errors": [{"path": field, "message": "Fill in this field."}],
    }
    assert repository.get(request.id) is None


def test_example_14_a_take5_with_no_hazards_cannot_be_submitted(
    client: TestClient,
) -> None:
    """Every Take 5 has at least one hazard (R5)."""
    request = SubmissionRequest(
        id=uuid4(),
        draft=sample_draft().model_copy(update={"hazards": ()}),
    )

    response: Response = client.post(
        "/api/take5s",
        json=request.model_dump(mode="json"),
    )

    assert response.status_code == 422
    assert response.json()["errors"] == [
        {"path": "hazards", "message": "List at least one hazard."},
    ]


def test_an_unknown_id_is_a_404_with_a_message(client: TestClient) -> None:
    """A link to a Take 5 that doesn't exist gets a message a person can read."""
    response: Response = client.get(f"/api/take5s/{uuid4()}")

    assert response.status_code == 404
    assert response.json() == {"detail": "This Take 5 could not be found."}


def test_an_id_that_is_not_a_uuid_is_a_422_in_the_form_errors_shape(
    client: TestClient,
) -> None:
    """A malformed ID gets the same 422 shape as a gap in the form."""
    response: Response = client.get("/api/take5s/not-a-uuid")

    assert response.status_code == 422
    body: dict[str, Any] = response.json()
    assert body["detail"] == "Some of what was sent could not be read."
    assert [error["path"] for error in body["errors"]] == ["take5_id"]


def test_a_submission_without_an_id_is_a_422_in_the_form_errors_shape(
    client: TestClient,
) -> None:
    """A body FastAPI can't read gets the declared 422 shape, not FastAPI's own."""
    response: Response = client.post(
        "/api/take5s",
        json={"draft": sample_draft().model_dump(mode="json")},
    )

    assert response.status_code == 422
    assert [error["path"] for error in response.json()["errors"]] == ["id"]


def test_reusing_an_id_for_other_answers_is_a_409_with_a_message(
    client: TestClient,
) -> None:
    """The first Take 5 saved with an ID is kept, and the second is told why."""
    request = SubmissionRequest(id=uuid4(), draft=sample_draft())
    client.post("/api/take5s", json=request.model_dump(mode="json"))
    changed = SubmissionRequest(
        id=request.id,
        draft=sample_draft().model_copy(update={"location": "Example pit"}),
    )

    response: Response = client.post(
        "/api/take5s",
        json=changed.model_dump(mode="json"),
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "This Take 5 was already saved with different answers.",
    }


def test_an_unreadable_draft_field_is_named_by_its_own_path(client: TestClient) -> None:
    """A field FastAPI can't read gets the path the form uses, and a plain message."""
    body: dict[str, Any] = SubmissionRequest(
        id=uuid4(),
        draft=sample_draft(),
    ).model_dump(
        mode="json",
    )
    body["draft"]["worker_name"] = 7

    response: Response = client.post("/api/take5s", json=body)

    assert response.status_code == 422
    assert response.json()["errors"] == [
        {"path": "worker_name", "message": "This answer could not be read."},
    ]


def test_example_22_a_draft_with_a_warning_can_still_be_submitted(
    client: TestClient,
) -> None:
    """The check warns about the hazard with no controls; the save still says why."""
    draft: Take5Draft = sample_uncontrolled_draft()

    check: Response = client.post("/api/take5s/check", json=draft.model_dump())
    saved: dict[str, Any] = finish(client, draft)

    assert check.json()["can_submit"] is True
    assert check.json()["warnings"] == [
        {
            "path": "hazards.0.controls",
            "message": "No controls: you'll be told not to start.",
        },
    ]
    assert saved["take5"]["verdict"] == {
        "can_start": False,
        "reasons": ["Say how you will control: Moving wheel"],
    }


def test_a_fix_and_the_take5_it_fixes_link_to_each_other(client: TestClient) -> None:
    """Each links to the other, and the first is kept exactly as it was saved."""
    first_saved: dict[str, Any] = finish(client, sample_uncontrolled_draft())
    first_id: UUID = UUID(first_saved["take5"]["id"])
    fix = SubmissionRequest(
        id=uuid4(),
        draft=sample_draft().model_copy(update={"fixes": first_id}),
    )

    fix_saved: Response = client.post("/api/take5s", json=fix.model_dump(mode="json"))
    reopened: dict[str, Any] = client.get(f"/api/take5s/{first_id}").json()

    assert fix_saved.json()["take5"]["fixes"] == str(first_id)
    assert fix_saved.json()["fixed_by"] is None
    assert fix_saved.json()["offers_fix"] is False
    assert first_saved["fixed_by"] is None
    assert first_saved["offers_fix"] is True
    assert reopened["fixed_by"] == str(fix.id)
    assert reopened["offers_fix"] is False
    assert reopened["take5"] == first_saved["take5"]


def test_a_fix_of_an_unknown_take5_is_a_422_on_the_fixes_field(
    client: TestClient,
    repository: SqliteTake5Repository,
) -> None:
    """A `fixes` ID that isn't a saved Take 5 is refused, and nothing is saved."""
    request = SubmissionRequest(
        id=uuid4(),
        draft=sample_draft().model_copy(update={"fixes": uuid4()}),
    )

    response: Response = client.post(
        "/api/take5s",
        json=request.model_dump(mode="json"),
    )

    assert response.status_code == 422
    assert response.json()["errors"] == [
        {"path": "fixes", "message": "The Take 5 this fixes could not be found."},
    ]
    assert repository.get(request.id) is None


def test_example_19_a_no_to_a_stop_question_is_saved_and_stops_the_job(
    client: TestClient,
) -> None:
    """The answers are saved with the Take 5, and a No gives the V1 reason."""
    answers: dict[str, Answer] = sample_answers(permits=Answer.NO)
    draft: Take5Draft = sample_draft().model_copy(update={"answers": answers})

    saved: Take5Response = Take5Response.model_validate(finish(client, draft))

    assert saved.take5.answers == answers
    assert saved.take5.verdict is not None
    assert not saved.take5.verdict.can_start
    assert saved.take5.verdict.reasons == (
        "You answered No to: Do you have the necessary permits? Sort this out first.",
    )


def test_an_answer_that_is_not_yes_no_or_na_is_a_field_error(
    client: TestClient,
) -> None:
    """Only the three answers are accepted, and the error names the question."""
    draft: dict[str, Any] = sample_draft().model_dump(mode="json")
    draft["answers"]["permits"] = "Maybe"

    response: Response = client.post("/api/take5s/check", json=draft)

    assert response.status_code == 422
    paths: list[str] = [error["path"] for error in response.json()["errors"]]
    assert paths == ["answers.permits"]


def test_a_draft_older_than_two_hours_is_named_as_run_out(client: TestClient) -> None:
    """The check and the submission both refuse a draft past the booklet's limit."""
    started_at: datetime = datetime.now(UTC) - timedelta(hours=2, minutes=1)
    draft: Take5Draft = sample_draft().model_copy(update={"started_at": started_at})

    checked: Response = client.post(
        "/api/take5s/check",
        json=draft.model_dump(mode="json"),
    )
    submitted: Response = client.post(
        "/api/take5s",
        json=SubmissionRequest(id=uuid4(), draft=draft).model_dump(mode="json"),
    )

    assert checked.status_code == 200
    assert [error["path"] for error in checked.json()["errors"]] == ["started_at"]
    assert submitted.status_code == 422
    assert [error["path"] for error in submitted.json()["errors"]] == ["started_at"]


def test_the_start_time_comes_back_with_the_saved_take5(client: TestClient) -> None:
    """A Take 5 started a few minutes ago is saved with its start time (K3)."""
    started_at: datetime = datetime.now(UTC) - timedelta(minutes=3)
    draft: Take5Draft = sample_draft().model_copy(update={"started_at": started_at})

    response: Response = client.post(
        "/api/take5s",
        json=SubmissionRequest(id=uuid4(), draft=draft).model_dump(mode="json"),
    )

    saved: Take5Response = Take5Response.model_validate(response.json())
    assert saved.take5.started_at == started_at


def test_a_start_time_without_a_time_zone_is_refused(client: TestClient) -> None:
    """A time with no zone can't be compared with the server's clock, so it is a 422."""
    draft: dict[str, Any] = sample_draft().model_dump(mode="json")

    response: Response = client.post(
        "/api/take5s/check",
        json={**draft, "started_at": "2026-11-15T20:12:00"},
    )

    assert response.status_code == 422
    assert [error["path"] for error in response.json()["errors"]] == ["started_at"]


def test_a_yes_needs_a_linked_hazard_and_the_link_is_saved(client: TestClient) -> None:
    """T5 through the API: refused without a link, saved and reopened with one."""
    heights_yes: Take5Draft = sample_draft().model_copy(
        update={"answers": sample_answers(heights=Answer.YES)},
    )
    unlinked = SubmissionRequest(id=uuid4(), draft=heights_yes)
    refused: Response = client.post(
        "/api/take5s",
        json=unlinked.model_dump(mode="json"),
    )
    assert refused.status_code == 422
    assert [error["path"] for error in refused.json()["errors"]] == ["answers.heights"]

    linked_hazard: HazardDraft = heights_yes.hazards[0].model_copy(
        update={"covers": ("heights",)},
    )
    linked = SubmissionRequest(
        id=uuid4(),
        draft=heights_yes.model_copy(update={"hazards": (linked_hazard,)}),
    )
    saved: Response = client.post("/api/take5s", json=linked.model_dump(mode="json"))
    assert saved.status_code == 200
    reopened: Response = client.get(f"/api/take5s/{linked.id}")
    assert reopened.json()["take5"]["hazards"][0]["covers"] == ["heights"]
