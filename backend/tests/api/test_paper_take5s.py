"""Integration tests for saving paper cards and ranking a batch (P1 to P6, F10)."""

from typing import Any
from uuid import uuid4

from fastapi.testclient import TestClient
from httpx2 import Response

from risk_assessment.domain.take5.fix import FROM_PAPER_MESSAGE
from risk_assessment.domain.take5.paper import BAD_LEVEL_MESSAGE, BAD_ZONE_MESSAGE
from risk_assessment.domain.take5.saved import SavedTake5
from risk_assessment.domain.take5.verdict import NO_HAZARD_REASON
from risk_assessment.storage.sqlite import SqliteTake5Repository
from tests.samples import sample_answers

WHEEL: str = "The wheel falls off the hub onto a foot"


def paper_request(
    hazards: list[dict[str, Any]] | None = None,
    **changed: Any,  # noqa: ANN401 - any field of the request
) -> dict[str, Any]:
    """Write what the scan page sends to save one checked card.

    Args:
        hazards: The card's hazards; none when left out.
        **changed: Request fields to replace.

    Returns:
        The request body.
    """
    request: dict[str, Any] = {
        "id": str(uuid4()),
        "draft": {
            "worker_name": "Sam Example",
            "job": "Change the front tyre on LV12",
            "location": "Workshop bay 2",
            "answers": {key: value.value for key, value in sample_answers().items()},
            "hazards": hazards or [],
        },
        "filled_in_at": "2026-04-03",
        "time_zone": "Australia/Perth",
    }
    return request | changed


def rated_hazard(likelihood: str = "Possible") -> dict[str, Any]:
    """Write a hazard rated before controls only, as many paper cards are.

    Args:
        likelihood: Its likelihood before controls, with a Major consequence.

    Returns:
        The hazard as the page sends it.
    """
    return {
        "description": WHEEL,
        "before": {"likelihood": likelihood, "consequence": "Major"},
    }


def saved_id(client: TestClient, request: dict[str, Any]) -> str:
    """Save a checked card and give its ID.

    Args:
        client: The app.
        request: What the page sends.

    Returns:
        The saved card's ID.
    """
    return client.post("/api/take5s/paper", json=request).json()["take5"]["id"]


def test_a_checked_card_is_saved_finished_from_paper_with_no_question(
    client: TestClient,
    repository: SqliteTake5Repository,
) -> None:
    """P1, P3, P5: saved as written, with its verdict and the card's date."""
    request: dict[str, Any] = paper_request()

    response: Response = client.post("/api/take5s/paper", json=request)

    assert response.status_code == 200
    body: dict[str, Any] = response.json()
    assert body["rating"] is None
    take5: dict[str, Any] = body["take5"]
    assert take5["from_paper"] is True
    assert take5["challenge"] is None
    assert take5["verdict"] == {"can_start": False, "reasons": [NO_HAZARD_REASON]}
    assert take5["started_at"] == "2026-04-03T00:00:00+08:00"
    saved: SavedTake5 | None = repository.get(take5["id"])
    assert saved is not None
    assert saved.from_paper
    assert saved.is_finished


def test_a_retry_returns_the_first_save_and_other_answers_conflict(
    client: TestClient,
) -> None:
    """The page's ID makes a retry safe, as for any Take 5."""
    request: dict[str, Any] = paper_request()
    first: Response = client.post("/api/take5s/paper", json=request)

    again: Response = client.post("/api/take5s/paper", json=request)
    changed: Response = client.post(
        "/api/take5s/paper",
        json=request | {"draft": request["draft"] | {"job": "Something else"}},
    )

    assert again.status_code == 200
    assert again.json()["take5"]["created_at"] == first.json()["take5"]["created_at"]
    assert changed.status_code == 409


def test_a_level_or_zone_no_card_has_is_a_422_beside_its_field(
    client: TestClient,
) -> None:
    """Only what no card can hold is refused, and the page is told where (P1)."""
    bad_level: Response = client.post(
        "/api/take5s/paper",
        json=paper_request([rated_hazard("Sometimes")]),
    )
    bad_zone: Response = client.post(
        "/api/take5s/paper",
        json=paper_request(time_zone="Mars/Olympus"),
    )

    assert bad_level.status_code == 422
    assert bad_level.json()["errors"] == [
        {"path": "hazards.0.before.likelihood", "message": BAD_LEVEL_MESSAGE},
    ]
    assert bad_zone.status_code == 422
    assert bad_zone.json()["errors"] == [
        {"path": "time_zone", "message": BAD_ZONE_MESSAGE},
    ]


def test_an_answer_to_a_question_the_card_lacks_is_a_422(client: TestClient) -> None:
    """A made-up question is never kept, and never a server error."""
    request: dict[str, Any] = paper_request()
    request["draft"]["answers"]["made_up"] = "Yes"

    response: Response = client.post("/api/take5s/paper", json=request)

    assert response.status_code == 422
    assert response.json()["errors"][0]["path"] == "answers.made_up"


def test_the_saved_list_says_which_came_from_paper(client: TestClient) -> None:
    """P6: the list marks a paper card."""
    client.post("/api/take5s/paper", json=paper_request())

    listed: list[dict[str, Any]] = client.get("/api/take5s").json()["take5s"]

    assert [line["from_paper"] for line in listed] == [True]


def test_a_batch_is_ranked_on_its_own_worst_first(client: TestClient) -> None:
    """F10: only the batch is ranked, worst first; an unknown ID is left out."""
    other: str = saved_id(client, paper_request())
    low: str = saved_id(client, paper_request([rated_hazard("Rare")]))
    high: str = saved_id(client, paper_request([rated_hazard("Likely")]))

    response: Response = client.post(
        "/api/ranked-take5s/batch",
        json={"ids": [low, high, str(uuid4())]},
    )

    assert response.status_code == 200
    body: dict[str, Any] = response.json()
    assert [line["id"] for line in body["take5s"]] == [high, low]
    assert other not in {line["id"] for line in body["take5s"]}
    assert body["best"] is None
    assert body["typical_minutes"] is None
    assert body["take5s"][0]["line"].startswith("Highest risk 21 Extreme.")
    assert body["take5s"][0]["from_paper"] is True
    assert body["take5s"][0]["started_at"] == "2026-04-03T00:00:00+08:00"


def test_a_batch_of_more_than_200_is_a_422(client: TestClient) -> None:
    """A batch is a pile of cards, not every Take 5 there is."""
    response: Response = client.post(
        "/api/ranked-take5s/batch",
        json={"ids": [str(uuid4()) for _ in range(201)]},
    )

    assert response.status_code == 422


def test_a_retry_of_a_card_dated_in_a_repeated_hour_is_not_a_conflict(
    client: TestClient,
) -> None:
    """Sydney's clocks go back at 3 am on 5 April 2026, so 2:30 happens twice (P5)."""
    request: dict[str, Any] = paper_request(
        filled_in_at="2026-04-05T02:30",
        time_zone="Australia/Sydney",
    )

    first: Response = client.post("/api/take5s/paper", json=request)
    again: Response = client.post("/api/take5s/paper", json=request)

    assert (first.status_code, again.status_code) == (200, 200)
    assert first.json()["take5"]["started_at"] == "2026-04-05T02:30:00+11:00"


def test_a_stopped_paper_card_offers_no_fix_and_cannot_be_fixed(
    client: TestClient,
) -> None:
    """Whoever checks a paper card isn't the worker who wrote it (P6, D126)."""
    take5_id: str = saved_id(client, paper_request())
    opened: dict[str, Any] = client.get(f"/api/take5s/{take5_id}").json()

    fix: Response = client.post(
        "/api/take5s",
        json={
            "id": str(uuid4()),
            "draft": paper_request()["draft"] | {"fixes": take5_id},
        },
    )

    assert opened["take5"]["verdict"]["can_start"] is False
    assert opened["offers_fix"] is False
    assert fix.status_code == 422
    assert {"path": "fixes", "message": FROM_PAPER_MESSAGE} in fix.json()["errors"]
