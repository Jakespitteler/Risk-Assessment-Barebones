"""Integration tests for the saved Take 5 list (spec F5)."""

from datetime import timedelta
from typing import Any
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from httpx2 import Response

from risk_assessment.api.app import create_app
from risk_assessment.domain.take5.saved import SavedTake5
from risk_assessment.domain.take5.verdict import Verdict
from risk_assessment.services.take5s import SAVED_LIST_PAGE_SIZE
from risk_assessment.storage.sqlite import SqliteTake5Repository
from tests.api.take5_requests import finish, submit
from tests.samples import sample_draft, sample_saved_take5, sample_uncontrolled_draft


def test_the_list_is_newest_first_with_the_date_worker_job_and_verdict(
    client: TestClient,
) -> None:
    """Each line has what the list screen shows, and nothing more of the card."""
    stopped: dict[str, Any] = finish(client, sample_uncontrolled_draft())["take5"]
    good_to_go: dict[str, Any] = finish(
        client,
        sample_draft().model_copy(update={"job": "Another example tyre job"}),
    )["take5"]

    response: Response = client.get("/api/take5s")

    assert response.status_code == 200
    assert response.json()["next"] is None
    assert response.json()["take5s"] == [
        {
            "id": good_to_go["id"],
            "created_at": good_to_go["created_at"],
            "worker_name": "Sam Example",
            "job": "Another example tyre job",
            "can_start": True,
            "fixed": False,
        },
        {
            "id": stopped["id"],
            "created_at": stopped["created_at"],
            "worker_name": "Sam Example",
            "job": "Change tyre on LV12",
            "can_start": False,
            "fixed": False,
        },
    ]


def test_the_list_sends_the_verdict_saved_not_one_worked_out_again(
    client: TestClient,
    repository: SqliteTake5Repository,
) -> None:
    """A Take 5 stopped by an older rule still lists as Don't start yet.

    Its one hazard is controlled, so today's rules would say Good to go.
    """
    stopped_by_an_older_rule = Verdict(
        can_start=False,
        reasons=("An older rule stopped this job.",),
    )
    repository.add(sample_saved_take5(verdict=stopped_by_an_older_rule))

    listed: list[dict[str, Any]] = client.get("/api/take5s").json()["take5s"]

    assert [line["can_start"] for line in listed] == [False]


def test_a_dont_start_yet_with_a_fix_is_marked_fixed(client: TestClient) -> None:
    """The fixed one says so, so a sorted-out Don't start yet isn't taken as open."""
    stopped: dict[str, Any] = finish(client, sample_uncontrolled_draft())["take5"]
    finish(client, sample_draft().model_copy(update={"fixes": UUID(stopped["id"])}))

    listed: list[dict[str, Any]] = client.get("/api/take5s").json()["take5s"]

    assert [(line["can_start"], line["fixed"]) for line in listed] == [
        (True, False),
        (False, True),
    ]


def test_a_fix_that_also_says_dont_start_yet_still_marks_its_original_fixed(
    client: TestClient,
) -> None:
    """Fixed means a newer Take 5 fixes it, whatever that one's verdict (spec D16)."""
    stopped: dict[str, Any] = finish(client, sample_uncontrolled_draft())["take5"]
    finish(
        client,
        sample_uncontrolled_draft().model_copy(
            update={"fixes": UUID(stopped["id"])},
        ),
    )

    listed: list[dict[str, Any]] = client.get("/api/take5s").json()["take5s"]

    assert [(line["can_start"], line["fixed"]) for line in listed] == [
        (False, False),
        (False, True),
    ]


def test_an_unfinished_take5_lists_with_no_verdict(client: TestClient) -> None:
    """Until its question is answered a Take 5 has no verdict (spec F5, C6)."""
    submit(client, sample_draft())

    listed: list[dict[str, Any]] = client.get("/api/take5s").json()["take5s"]

    assert [line["can_start"] for line in listed] == [None]


def test_an_unfinished_fix_still_marks_its_original_fixed(client: TestClient) -> None:
    """A saved fix counts at once, so a second fix can't be started beside it."""
    stopped: dict[str, Any] = finish(client, sample_uncontrolled_draft())["take5"]
    submit(client, sample_draft().model_copy(update={"fixes": UUID(stopped["id"])}))

    listed: list[dict[str, Any]] = client.get("/api/take5s").json()["take5s"]

    assert [(line["can_start"], line["fixed"]) for line in listed] == [
        (None, False),
        (False, True),
    ]


def test_the_list_is_empty_before_anything_is_saved(client: TestClient) -> None:
    """A new app sends an empty list, not an error."""
    response: Response = client.get("/api/take5s")

    assert response.status_code == 200
    assert response.json() == {"take5s": [], "next": None}


def test_show_more_carries_on_after_the_last_one_shown(
    client: TestClient,
    repository: SqliteTake5Repository,
) -> None:
    """The first page is the newest 50; `before` its `next` gets the rest (D18, D81)."""
    first: SavedTake5 = sample_saved_take5()
    for minute in range(SAVED_LIST_PAGE_SIZE + 2):
        repository.add(
            sample_saved_take5().model_copy(
                update={"created_at": first.created_at + timedelta(minutes=minute)},
            ),
        )

    first_page: dict[str, Any] = client.get("/api/take5s").json()
    second_page: dict[str, Any] = client.get(
        "/api/take5s",
        params={"before": first_page["next"]},
    ).json()

    assert len(first_page["take5s"]) == SAVED_LIST_PAGE_SIZE
    assert first_page["next"] == first_page["take5s"][-1]["id"]
    assert len(second_page["take5s"]) == 2
    assert second_page["next"] is None
    assert (
        second_page["take5s"][0]["created_at"] < first_page["take5s"][-1]["created_at"]
    )


def test_a_before_that_is_not_an_id_is_refused(client: TestClient) -> None:
    """FastAPI checks the ID's shape, so a mistyped link gets 422, not a crash."""
    assert client.get("/api/take5s", params={"before": "not-an-id"}).status_code == 422


def test_a_before_that_is_not_saved_gives_an_empty_last_page(
    client: TestClient,
    repository: SqliteTake5Repository,
) -> None:
    """An unknown `before` lists nothing after it, not the whole list again."""
    repository.add(sample_saved_take5())

    response: Response = client.get("/api/take5s", params={"before": str(uuid4())})

    assert response.status_code == 200
    assert response.json() == {"take5s": [], "next": None}


def test_no_endpoint_changes_a_saved_take5() -> None:
    """Spec F5: a saved Take 5 can only be read. No route edits, replaces or deletes it.

    Saving again with the same ID returns the first save (see the retry tests). The
    only routes that write add a new Take 5, or answer an unfinished one's question
    once (spec C6). The check, the nudges, the ranking and risk by area save nothing.
    """
    paths: dict[str, dict[str, Any]] = create_app().openapi()["paths"]

    methods: dict[str, set[str]] = {path: set(item) for path, item in paths.items()}

    assert methods == {
        "/api/take5/template": {"get"},
        "/api/take5s/check": {"post"},
        "/api/take5s/nudges": {"post"},
        "/api/take5s": {"get", "post"},
        "/api/take5s/{take5_id}": {"get"},
        "/api/take5s/{take5_id}/answer": {"post"},
        "/api/ranked-take5s": {"get"},
        "/api/risk-by-area": {"get"},
    }


def test_editing_or_deleting_a_saved_take5_is_refused(client: TestClient) -> None:
    """Each way HTTP has to change a resource gets 405, and the Take 5 is unchanged."""
    saved: dict[str, Any] = finish(client, sample_draft())["take5"]
    path: str = f"/api/take5s/{saved['id']}"

    refusals: list[int] = [
        client.put(path, json={}).status_code,
        client.patch(path, json={}).status_code,
        client.delete(path).status_code,
    ]

    assert refusals == [405, 405, 405]
    assert client.get(path).json()["take5"] == saved
