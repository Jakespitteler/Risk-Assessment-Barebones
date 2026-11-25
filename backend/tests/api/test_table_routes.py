"""Integration tests for the Take 5 table and its CSV export (spec E1 to E6)."""

from typing import Any

from fastapi.testclient import TestClient
from httpx2 import Response

from risk_assessment.storage.sqlite import SqliteTake5Repository
from tests.domain.take5.test_ranking import ranked_take5
from tests.domain.take5.test_table import SATURDAY_MORNING, started

PERTH: dict[str, str] = {"zone": "Australia/Perth"}


def test_the_table_lists_every_take5_most_important_first(
    client: TestClient,
    repository: SqliteTake5Repository,
) -> None:
    """E1, E2: every saved one is a row, with the filters' choices beside them."""
    repository.add(started(SATURDAY_MORNING))
    repository.add(
        started(SATURDAY_MORNING, ranked_take5(before=("Possible", "Major"))),
    )

    response: Response = client.get("/api/take5-table", params=PERTH)

    assert response.status_code == 200
    body: dict[str, Any] = response.json()
    assert [row["importance"] for row in body["rows"]] == [18, 8]
    assert body["rows"][1]["weekday"] == "Saturday"
    assert body["areas"] == ["Example workshop"]
    # Only the bands some Take 5 has, lowest first (E6).
    assert body["bands"] == ["Moderate", "Extreme"]
    assert body["verdicts"] == ["Good to go"]
    assert body["weekdays"][0] == "Monday"
    assert body["times_of_day"] == [
        "Midnight to 6 am",
        "6 am to noon",
        "Noon to 6 pm",
        "6 pm to midnight",
    ]


def test_the_filters_narrow_the_rows(
    client: TestClient,
    repository: SqliteTake5Repository,
) -> None:
    """E4: the query's filters keep only matching rows."""
    repository.add(started(SATURDAY_MORNING))
    repository.add(
        started(SATURDAY_MORNING, ranked_take5(before=("Possible", "Major"))),
    )

    rows: list[dict[str, Any]] = client.get(
        "/api/take5-table",
        params=PERTH | {"band": "Extreme", "from": "2026-11-21", "to": "2026-11-21"},
    ).json()["rows"]

    assert [row["highest_band"] for row in rows] == ["Extreme"]


def test_the_csv_is_a_download_of_the_same_rows(
    client: TestClient,
    repository: SqliteTake5Repository,
) -> None:
    """E5: a CSV attachment with a header and one line per row kept."""
    repository.add(started(SATURDAY_MORNING))

    response: Response = client.get(
        "/api/take5-table.csv",
        params=PERTH | {"search": "tyre"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.headers["content-disposition"].startswith(
        'attachment; filename="take5s-',
    )
    lines: list[str] = response.text.lstrip(
        "\N{ZERO WIDTH NO-BREAK SPACE}",
    ).splitlines()
    assert lines[0].startswith("Started,Saved,Month,Weekday")
    assert len(lines) == 2


def test_an_unknown_zone_or_date_is_a_422(client: TestClient) -> None:
    """A filter or zone that can't be read is a form error, never a server error."""
    zone: Response = client.get("/api/take5-table", params={"zone": "Mars/Olympus"})
    day: Response = client.get(
        "/api/take5-table.csv",
        params=PERTH | {"from": "21/11/2026"},
    )

    assert (zone.status_code, day.status_code) == (422, 422)
    assert [error["path"] for error in zone.json()["errors"]] == ["zone"]


def test_a_blank_filter_keeps_every_row(
    client: TestClient,
    repository: SqliteTake5Repository,
) -> None:
    """E4: a plain form sends empty filters, which narrow nothing."""
    repository.add(started(SATURDAY_MORNING))
    blank: dict[str, str] = {
        name: ""
        for name in (
            "search",
            "from",
            "to",
            "verdict",
            "band",
            "area",
            "weekday",
            "time_of_day",
            "from_paper",
            "job",
            "worker",
            "importance",
            "thought_gaps",
        )
    }
    spaces: dict[str, str] = {
        name: " "
        for name in (
            "verdict",
            "band",
            "weekday",
            "time_of_day",
            "importance",
            "thought_gaps",
        )
    }

    response: Response = client.get("/api/take5-table", params=PERTH | blank)
    spaced: Response = client.get("/api/take5-table", params=PERTH | spaces)

    assert response.status_code == 200
    assert len(response.json()["rows"]) == 1
    assert len(spaced.json()["rows"]) == 1


def test_the_column_filters_narrow_the_rows_and_the_csv(
    client: TestClient,
    repository: SqliteTake5Repository,
) -> None:
    """E6: several ticked values per column narrow both, and each list is sent."""
    repository.add(started(SATURDAY_MORNING))
    repository.add(
        started(SATURDAY_MORNING, ranked_take5(description="Moving wheel")),
    )
    ticked: dict[str, str | list[str]] = PERTH | {
        "job": "change tyre on LV12",
        "worker": "Sam Example",
        "importance": ["13", "18"],
        "thought_gaps": ["Some gaps", "Rushed"],
    }

    page: dict[str, Any] = client.get("/api/take5-table", params=ticked).json()
    exported: Response = client.get("/api/take5-table.csv", params=ticked)

    assert [row["importance"] for row in page["rows"]] == [13]
    # Each list holds what the other filters leave, as a spreadsheet's does.
    assert page["thought_gap_choices"] == ["Some gaps"]
    assert page["jobs"] == ["Change tyre on LV12"]
    assert page["workers"] == ["Sam Example"]
    assert page["importances"] == [13]
    assert page["verdicts"] == ["Good to go"]
    assert len(exported.text.splitlines()) == 2


def test_an_importance_that_is_not_a_number_is_a_422(client: TestClient) -> None:
    """E6: "high" can't be read, so it is a form error."""
    response: Response = client.get(
        "/api/take5-table",
        params=PERTH | {"importance": "high"},
    )

    assert response.status_code == 422
