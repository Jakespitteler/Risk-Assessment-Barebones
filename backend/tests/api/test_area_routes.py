"""Integration tests for the risk-by-area endpoint (spec A1 to A5)."""

from datetime import datetime, timedelta
from typing import Any

from fastapi.testclient import TestClient
from httpx2 import Response

from risk_assessment.domain.questions import Answer
from risk_assessment.storage.sqlite import SqliteTake5Repository
from tests.domain.take5.test_areas import WORKSHOP, area_take5
from tests.services.test_areas import MIDNIGHT_TODAY

TODAY: str = MIDNIGHT_TODAY.isoformat()


def test_each_area_comes_with_its_counts_and_common_yes(
    client: TestClient,
    repository: SqliteTake5Repository,
) -> None:
    """A1 to A5: the page gets each area's name, numbers and Yes answers."""
    morning: datetime = MIDNIGHT_TODAY + timedelta(hours=7)
    repository.add(
        area_take5(before=("Possible", "Major"), heights=Answer.YES).model_copy(
            update={
                "started_at": morning,
                "created_at": morning + timedelta(minutes=10),
            },
        ),
    )

    response: Response = client.get("/api/risk-by-area", params={"today": TODAY})

    assert response.status_code == 200
    body: dict[str, Any] = response.json()
    assert body["areas"] == [
        {
            "name": WORKSHOP,
            "take5_count": 1,
            "high_risk_count": 1,
            "stopped_count": 0,
            "thought_gap_count": 0,
            "highest_score": 18,
            "highest_band": "Extreme",
            "common_yes": [
                {"question": "Will I be working at heights?", "count": 1},
            ],
        },
    ]


def test_nothing_in_the_30_days_gives_no_areas(client: TestClient) -> None:
    """A2: with nothing saved, the list of areas is empty."""
    body: dict[str, Any] = client.get(
        "/api/risk-by-area",
        params={"today": TODAY},
    ).json()

    assert body["areas"] == []


def test_a_moment_with_no_time_zone_is_refused(client: TestClient) -> None:
    """A2: midnight must say where the phone is, or 30 days can't be counted."""
    response: Response = client.get(
        "/api/risk-by-area",
        params={"today": "2026-11-21T00:00:00"},
    )

    assert response.status_code == 422
