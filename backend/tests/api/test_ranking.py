"""Integration tests for the ranking endpoint (spec W1 to W7)."""

from datetime import datetime, timedelta
from typing import Any

from fastapi.testclient import TestClient
from httpx2 import Response

from risk_assessment.api.app import create_app
from risk_assessment.domain.take5.saved import SavedTake5
from risk_assessment.settings import Settings
from risk_assessment.storage.sqlite import SqliteTake5Repository
from tests.domain.take5.test_ranking import ranked_take5
from tests.services.test_ranking import MIDNIGHT_IN_PERTH, SWAPPED, StandInRanker

SINCE: str = MIDNIGHT_IN_PERTH.astimezone().isoformat()


def test_the_ranking_lists_today_worst_first_with_names_and_lines(
    client: TestClient,
    repository: SqliteTake5Repository,
) -> None:
    """W1: each line has who, what, the verdict and why, worst first, with no AI."""
    morning: datetime = MIDNIGHT_IN_PERTH + timedelta(hours=7)
    careful: SavedTake5 = repository.add(ranked_take5(saved_at=morning))
    careless: SavedTake5 = repository.add(
        ranked_take5(answer=None, minutes_taken=1, saved_at=morning),
    )

    response: Response = client.get("/api/ranked-take5s", params={"since": SINCE})

    assert response.status_code == 200
    listed: list[dict[str, Any]] = response.json()["take5s"]
    assert [line["id"] for line in listed] == [str(careless.id), str(careful.id)]
    assert listed[0] == {
        "id": str(careless.id),
        "created_at": listed[0]["created_at"],
        "worker_name": "Sam Example",
        "job": "Change tyre on LV12",
        "can_start": None,
        "line": (
            "Highest risk 8 Moderate. The question was never answered; "
            "it was filled in in under 2 minutes."
        ),
        "ranked_by_ai": False,
    }


def test_the_ai_order_reaches_the_page(repository: SqliteTake5Repository) -> None:
    """W6: with an AI set up, its order and lines are sent, marked as the AI's."""
    morning: datetime = MIDNIGHT_IN_PERTH + timedelta(hours=7)
    careless: SavedTake5 = repository.add(
        ranked_take5(answer=None, minutes_taken=1, saved_at=morning),
    )
    careful: SavedTake5 = repository.add(ranked_take5(saved_at=morning))
    client = TestClient(
        create_app(repository, take5_ranker=StandInRanker(SWAPPED)),
    )

    listed: list[dict[str, Any]] = client.get(
        "/api/ranked-take5s",
        params={"since": SINCE},
    ).json()["take5s"]

    assert [(line["id"], line["line"], line["ranked_by_ai"]) for line in listed] == [
        (str(careful.id), "Copied controls.", True),
        (str(careless.id), "Rushed.", True),
    ]


def test_nothing_today_gives_an_empty_ranking(client: TestClient) -> None:
    """An empty day is an empty list, not an error."""
    response: Response = client.get("/api/ranked-take5s", params={"since": SINCE})

    assert response.json() == {"take5s": [], "today_only": False}


def test_a_moment_without_a_time_zone_is_refused(client: TestClient) -> None:
    """W7: midnight means nothing without the phone's time zone."""
    response: Response = client.get(
        "/api/ranked-take5s",
        params={"since": "2026-11-20T00:00:00"},
    )

    assert response.status_code == 422


def test_by_default_every_saved_take5_is_ranked(
    client: TestClient,
    repository: SqliteTake5Repository,
) -> None:
    """W7, D118: while the app is a proof of concept, yesterday's Take 5s count too."""
    yesterday: SavedTake5 = repository.add(
        ranked_take5(saved_at=MIDNIGHT_IN_PERTH - timedelta(hours=7)),
    )

    body: dict[str, Any] = client.get(
        "/api/ranked-take5s",
        params={"since": SINCE},
    ).json()

    assert [line["id"] for line in body["take5s"]] == [str(yesterday.id)]
    assert body["today_only"] is False


def test_the_setting_ranks_only_take5s_from_today(
    repository: SqliteTake5Repository,
) -> None:
    """W7, D118: `TAKE5_RANK_TODAY_ONLY` brings back the ranking by day."""
    repository.add(ranked_take5(saved_at=MIDNIGHT_IN_PERTH - timedelta(hours=7)))
    client = TestClient(
        create_app(repository, Settings(rank_today_only=True)),
    )

    body: dict[str, Any] = client.get(
        "/api/ranked-take5s",
        params={"since": SINCE},
    ).json()

    assert body == {"take5s": [], "today_only": True}
