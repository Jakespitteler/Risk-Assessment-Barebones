"""Integration tests for checking, submitting, retrying and reopening a Take 5."""

from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from httpx2 import Response

from risk_assessment.api.app import create_app
from risk_assessment.api.schemas import SubmissionRequest, Take5Response
from risk_assessment.domain.controls import ControlKind
from risk_assessment.domain.take5.draft import (
    ControlDraft,
    HazardDraft,
    RatingChoice,
    Take5Draft,
)
from risk_assessment.storage.sqlite import SqliteTake5Repository


def _draft() -> Take5Draft:
    """A fully specified example with one controlled hazard rated 8 then 5."""
    return Take5Draft(
        worker_name="Sam Example",
        job="Change tyre on LV12",
        location="Example workshop",
        hazards=(
            HazardDraft(
                description="Moving wheel",
                before=RatingChoice(likelihood="Possible", consequence="Minor"),
                controls=(
                    ControlDraft(
                        description="Barricade the work area",
                        kind=ControlKind.BARRICADE,
                    ),
                ),
                after=RatingChoice(likelihood="Unlikely", consequence="Minor"),
            ),
        ),
    )


def test_submit_and_reopen_preserve_the_original_document(tmp_path: Path) -> None:
    """A fresh repository instance retrieves the verdict, template and ratings."""
    database: Path = tmp_path / "take5.sqlite3"
    client = TestClient(create_app(SqliteTake5Repository(database)))
    request = SubmissionRequest(id=uuid4(), draft=_draft())
    response: Response = client.post(
        "/api/take5s", json=request.model_dump(mode="json")
    )
    assert response.status_code == 200
    saved: Take5Response = Take5Response.model_validate(response.json())
    assert saved.take5.verdict.can_start
    assert saved.rating.score == 5 and saved.rating.band == "Low"
    assert saved.take5.template.matrix.jha_threshold == 11
    reopened: Response = TestClient(create_app(SqliteTake5Repository(database))).get(
        f"/api/take5s/{request.id}"
    )
    assert reopened.json() == response.json()
    assert client.post(f"/api/take5s/{request.id}", json={}).status_code == 405


def test_retries_return_one_document_and_different_input_cannot_replace_it(
    tmp_path: Path,
) -> None:
    """A stable ID covers repeated clicks and a retry after a lost response."""
    client = TestClient(create_app(SqliteTake5Repository(tmp_path / "take5.sqlite3")))
    request = SubmissionRequest(id=uuid4(), draft=_draft())
    first: Response = client.post("/api/take5s", json=request.model_dump(mode="json"))
    retry: Response = client.post("/api/take5s", json=request.model_dump(mode="json"))
    assert retry.json() == first.json()
    changed: SubmissionRequest = request.model_copy(
        update={
            "draft": request.draft.model_copy(update={"job": "Another example job"})
        }
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
    assert paths == {"worker_name", "job", "location", "hazards"}
    assert not response.json()["can_submit"]
    assert not database.exists()


@pytest.mark.parametrize(
    "path", ["description", "before", "after", "control_description", "control_kind"]
)
def test_each_incomplete_hazard_field_blocks_submission(
    tmp_path: Path, path: str
) -> None:
    """The API reports the exact missing field and refuses to save the draft."""
    draft: Take5Draft = _draft()
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
    repository = SqliteTake5Repository(tmp_path / "take5.sqlite3")
    client = TestClient(create_app(repository))
    submission_id: UUID = uuid4()
    response: Response = client.post(
        "/api/take5s",
        json=SubmissionRequest(id=submission_id, draft=draft).model_dump(mode="json"),
    )
    assert response.status_code == 422
    assert response.json()["errors"][0]["path"].startswith("hazards.0.")
    assert repository.get(submission_id) is None


def test_without_controls_after_is_derived_and_the_verdict_stops_the_job(
    tmp_path: Path,
) -> None:
    """A hazard without controls can be submitted but must stop the job."""
    draft: Take5Draft = _draft()
    hazard: HazardDraft = draft.hazards[0].model_copy(
        update={"controls": (), "after": RatingChoice()}
    )
    request = SubmissionRequest(
        id=uuid4(), draft=draft.model_copy(update={"hazards": (hazard,)})
    )
    client = TestClient(create_app(SqliteTake5Repository(tmp_path / "take5.sqlite3")))
    response: Response = client.post(
        "/api/take5s", json=request.model_dump(mode="json")
    )
    saved: Take5Response = Take5Response.model_validate(response.json())
    assert not saved.take5.verdict.can_start
    assert saved.take5.hazards[0].after == saved.take5.hazards[0].before
    assert saved.rating.score == 8


def test_higher_after_risk_and_unknown_scale_choices_are_field_errors(
    tmp_path: Path,
) -> None:
    """A client cannot invent ratings or increase risk through controls."""
    client = TestClient(create_app(SqliteTake5Repository(tmp_path / "take5.sqlite3")))
    draft: Take5Draft = _draft()
    for after in (
        RatingChoice(likelihood="Almost Certain", consequence="Critical"),
        RatingChoice(likelihood="Invented", consequence="Minor"),
    ):
        hazard: HazardDraft = draft.hazards[0].model_copy(update={"after": after})
        response: Response = client.post(
            "/api/take5s/check",
            json=draft.model_copy(update={"hazards": (hazard,)}).model_dump(
                mode="json"
            ),
        )
        assert not response.json()["can_submit"]
        assert response.json()["errors"][0]["path"].startswith("hazards.0.after")


@pytest.mark.parametrize("field", ["worker_name", "job", "location"])
def test_a_blank_name_job_or_location_cannot_be_submitted(
    tmp_path: Path, field: str
) -> None:
    """Each blank field comes back as a 422 naming that field, and nothing is saved."""
    repository = SqliteTake5Repository(tmp_path / "take5.sqlite3")
    client = TestClient(create_app(repository))
    request = SubmissionRequest(
        id=uuid4(), draft=_draft().model_copy(update={field: " "})
    )

    response: Response = client.post(
        "/api/take5s", json=request.model_dump(mode="json")
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Fill in the highlighted fields before you submit.",
        "errors": [{"path": field, "message": "Fill in this field."}],
    }
    assert repository.get(request.id) is None


def test_example_14_a_take5_with_no_hazards_cannot_be_submitted(
    tmp_path: Path,
) -> None:
    """Every Take 5 has at least one hazard (R5)."""
    client = TestClient(create_app(SqliteTake5Repository(tmp_path / "take5.sqlite3")))
    request = SubmissionRequest(
        id=uuid4(), draft=_draft().model_copy(update={"hazards": ()})
    )

    response: Response = client.post(
        "/api/take5s", json=request.model_dump(mode="json")
    )

    assert response.status_code == 422
    assert response.json()["errors"] == [
        {"path": "hazards", "message": "List at least one hazard."}
    ]


def test_an_unknown_id_is_a_404_with_a_message(tmp_path: Path) -> None:
    """A link to a Take 5 that doesn't exist gets a message a person can read."""
    client = TestClient(create_app(SqliteTake5Repository(tmp_path / "take5.sqlite3")))

    response: Response = client.get(f"/api/take5s/{uuid4()}")

    assert response.status_code == 404
    assert response.json() == {"detail": "This Take 5 could not be found."}


def test_an_id_that_is_not_a_uuid_is_a_422_in_the_form_errors_shape(
    tmp_path: Path,
) -> None:
    """A malformed ID gets the same 422 shape as a gap in the form."""
    client = TestClient(create_app(SqliteTake5Repository(tmp_path / "take5.sqlite3")))

    response: Response = client.get("/api/take5s/not-a-uuid")

    assert response.status_code == 422
    body: dict[str, Any] = response.json()
    assert body["detail"] == "Some of what was sent could not be read."
    assert [error["path"] for error in body["errors"]] == ["take5_id"]


def test_a_submission_without_an_id_is_a_422_in_the_form_errors_shape(
    tmp_path: Path,
) -> None:
    """A body FastAPI can't read gets the declared 422 shape, not FastAPI's own."""
    client = TestClient(create_app(SqliteTake5Repository(tmp_path / "take5.sqlite3")))

    response: Response = client.post(
        "/api/take5s", json={"draft": _draft().model_dump(mode="json")}
    )

    assert response.status_code == 422
    assert [error["path"] for error in response.json()["errors"]] == ["id"]


def test_reusing_an_id_for_other_answers_is_a_409_with_a_message(
    tmp_path: Path,
) -> None:
    """The first Take 5 saved with an ID is kept, and the second is told why."""
    client = TestClient(create_app(SqliteTake5Repository(tmp_path / "take5.sqlite3")))
    request = SubmissionRequest(id=uuid4(), draft=_draft())
    client.post("/api/take5s", json=request.model_dump(mode="json"))
    changed = SubmissionRequest(
        id=request.id, draft=_draft().model_copy(update={"location": "Example pit"})
    )

    response: Response = client.post(
        "/api/take5s", json=changed.model_dump(mode="json")
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "This Take 5 was already saved with different answers."
    }


def test_an_unreadable_draft_field_is_named_by_its_own_path(tmp_path: Path) -> None:
    """A field FastAPI can't read gets the path the form uses, and a plain message."""
    client = TestClient(create_app(SqliteTake5Repository(tmp_path / "take5.sqlite3")))
    body: dict[str, Any] = SubmissionRequest(id=uuid4(), draft=_draft()).model_dump(
        mode="json"
    )
    body["draft"]["worker_name"] = 7

    response: Response = client.post("/api/take5s", json=body)

    assert response.status_code == 422
    assert response.json()["errors"] == [
        {"path": "worker_name", "message": "This answer could not be read."}
    ]


def _without_controls(draft: Take5Draft) -> Take5Draft:
    """Example 22: the draft with its one hazard left without controls.

    Args:
        draft: A draft with one hazard.

    Returns:
        The same draft, with that hazard's controls and after rating taken away.
    """
    hazard: HazardDraft = draft.hazards[0].model_copy(
        update={"controls": (), "after": RatingChoice()}
    )
    return draft.model_copy(update={"hazards": (hazard,)})


def test_example_22_a_draft_with_a_warning_can_still_be_submitted(
    tmp_path: Path,
) -> None:
    """The check warns about the hazard with no controls; the save still says why."""
    client = TestClient(create_app(SqliteTake5Repository(tmp_path / "take5.sqlite3")))
    draft: Take5Draft = _without_controls(_draft())

    check: Response = client.post("/api/take5s/check", json=draft.model_dump())
    saved: Response = client.post(
        "/api/take5s",
        json=SubmissionRequest(id=uuid4(), draft=draft).model_dump(mode="json"),
    )

    assert check.json()["can_submit"] is True
    assert check.json()["warnings"] == [
        {
            "path": "hazards.0.controls",
            "message": "No controls: you'll be told not to start.",
        }
    ]
    assert saved.status_code == 200
    assert saved.json()["take5"]["verdict"] == {
        "can_start": False,
        "reasons": ["Say how you will control: Moving wheel"],
    }


def test_a_fix_and_the_take5_it_fixes_link_to_each_other(tmp_path: Path) -> None:
    """Each links to the other, and the first is kept exactly as it was saved."""
    client = TestClient(create_app(SqliteTake5Repository(tmp_path / "take5.sqlite3")))
    first = SubmissionRequest(id=uuid4(), draft=_without_controls(_draft()))
    first_saved: dict[str, Any] = client.post(
        "/api/take5s", json=first.model_dump(mode="json")
    ).json()
    fix = SubmissionRequest(
        id=uuid4(), draft=_draft().model_copy(update={"fixes": first.id})
    )

    fix_saved: Response = client.post("/api/take5s", json=fix.model_dump(mode="json"))
    reopened: dict[str, Any] = client.get(f"/api/take5s/{first.id}").json()

    assert fix_saved.json()["take5"]["fixes"] == str(first.id)
    assert fix_saved.json()["fixed_by"] is None
    assert first_saved["fixed_by"] is None
    assert reopened["fixed_by"] == str(fix.id)
    assert reopened["take5"] == first_saved["take5"]


def test_a_fix_of_an_unknown_take5_is_a_422_on_the_fixes_field(tmp_path: Path) -> None:
    """A `fixes` ID that isn't a saved Take 5 is refused, and nothing is saved."""
    repository = SqliteTake5Repository(tmp_path / "take5.sqlite3")
    client = TestClient(create_app(repository))
    request = SubmissionRequest(
        id=uuid4(), draft=_draft().model_copy(update={"fixes": uuid4()})
    )

    response: Response = client.post(
        "/api/take5s", json=request.model_dump(mode="json")
    )

    assert response.status_code == 422
    assert response.json()["errors"] == [
        {"path": "fixes", "message": "The Take 5 this fixes could not be found."}
    ]
    assert repository.get(request.id) is None
