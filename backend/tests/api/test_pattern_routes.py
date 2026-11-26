"""Integration tests for the patterns-over-time endpoint (spec S1 to S5)."""

from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from fastapi.testclient import TestClient
from httpx2 import Response

from risk_assessment.domain.take5.saved import SavedTake5
from risk_assessment.storage.sqlite import SqliteTake5Repository
from tests.domain.take5.test_ranking import ranked_take5
from tests.domain.take5.test_table import SATURDAY_MORNING, started

PERTH: dict[str, str] = {"zone": "Australia/Perth"}
MONDAY_MORNING: datetime = SATURDAY_MORNING + timedelta(days=2)


def save(repository: SqliteTake5Repository, take5: SavedTake5, count: int) -> None:
    """Save several copies of a Take 5, each with its own ID.

    Args:
        repository: Where to save them.
        take5: The Take 5 to copy.
        count: How many to save.
    """
    for _ in range(count):
        repository.add(take5.model_copy(update={"id": uuid4()}))


def test_the_page_gets_the_sentences_and_the_counts(
    client: TestClient,
    repository: SqliteTake5Repository,
) -> None:
    """S1 to S5: high-risk Take 5s stand out on Mondays, linked to Mondays."""
    high_risk: SavedTake5 = ranked_take5(before=("Possible", "Major"))
    save(repository, started(MONDAY_MORNING, high_risk), 3)
    save(repository, started(MONDAY_MORNING), 2)
    save(repository, started(SATURDAY_MORNING), 5)

    response: Response = client.get("/api/patterns", params=PERTH)

    assert response.status_code == 200
    body: dict[str, Any] = response.json()
    assert body["take5_count"] == 10
    assert {
        "text": (
            "3 of 5 Take 5s on Mondays were high risk, and none of 5 on other days."
        ),
        "table_filters": {"weekday": "Monday"},
    } in body["sentences"]
    assert body["by_weekday"][0] == {
        "group": "Monday",
        "take5_count": 5,
        "high_risk_count": 3,
        "rushed_count": 0,
        "thought_gaps_count": 0,
        "stopped_count": 0,
    }
    assert body["by_month"][0]["group"] == "November 2026"
    assert body["no_time_of_day_count"] == 0


def test_with_nothing_saved_there_is_nothing_to_say(client: TestClient) -> None:
    """S1: no Take 5s, no sentences."""
    body: dict[str, Any] = client.get("/api/patterns", params=PERTH).json()

    assert body["take5_count"] == 0
    assert body["sentences"] == []


def test_an_unknown_zone_is_a_422(client: TestClient) -> None:
    """E3: the zone must be one the server knows."""
    response: Response = client.get("/api/patterns", params={"zone": "Mars/Olympus"})

    assert response.status_code == 422
