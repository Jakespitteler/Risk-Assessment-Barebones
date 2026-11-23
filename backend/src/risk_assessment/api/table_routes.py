"""The Take 5 table and its CSV export, turning HTTP into a service call (E1 to E5)."""

from datetime import date, datetime
from typing import Annotated, Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, Query, Response
from pydantic import AfterValidator

from risk_assessment.api.schemas import FormErrors, Take5TablePage
from risk_assessment.domain.take5.table import Take5Filters
from risk_assessment.services.take5_table import Take5Table, Take5TableService

_UNREADABLE: dict[int | str, dict[str, Any]] = {
    422: {"model": FormErrors, "description": "A filter or the zone can't be read"},
}


def _known_zone(name: str) -> str:
    """Refuse a time zone that isn't known.

    Args:
        name: An IANA name, such as "Australia/Perth".

    Returns:
        The name.

    Raises:
        ValueError: If no such zone is known.
    """
    try:
        ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError) as error:
        message = "This time zone isn't known."
        raise ValueError(message) from error
    return name


type ZoneName = Annotated[str, AfterValidator(_known_zone)]


def _filters(  # noqa: PLR0913 - one argument per filter on the page
    search: str = "",
    start: Annotated[date | None, Query(alias="from")] = None,
    end: Annotated[date | None, Query(alias="to")] = None,
    verdict: str | None = None,
    band: str | None = None,
    area: str | None = None,
    weekday: str | None = None,
    time_of_day: str | None = None,
    from_paper: bool | None = None,
) -> Take5Filters:
    """Read the filters from the query (E4). An empty one lets every row through.

    Args:
        search: Words to find in the job, location or worker.
        start: The first day to show.
        end: The last day to show.
        verdict: Such as "Don't start yet".
        band: A risk band, such as "Extreme".
        area: An area, as typed.
        weekday: Such as "Monday".
        time_of_day: Such as "6 am to noon".
        from_paper: True for paper cards only, False for none.

    Returns:
        The filters.
    """
    return Take5Filters(
        search=search,
        start=start,
        end=end,
        verdict=verdict or None,
        band=band or None,
        area=area or None,
        weekday=weekday or None,
        time_of_day=time_of_day or None,
        from_paper=from_paper,
    )


def create_table_router(service: Take5TableService) -> APIRouter:
    """Bind the table and its export to the service that the composition root built.

    Args:
        service: The table service the endpoints call.

    Returns:
        The router with both endpoints.
    """
    router = APIRouter(tags=["table"])

    @router.get("/api/take5-table", responses=_UNREADABLE)
    def take5_table(
        zone: ZoneName,
        filters: Annotated[Take5Filters, Depends(_filters)],
    ) -> Take5TablePage:
        """Lay out every saved Take 5 as a row, the most important first (E1 to E4).

        Args:
            zone: The page's time zone, for a Take 5 with no start time.
            filters: What to narrow the table to.
        """
        table: Take5Table = service.table(filters, ZoneInfo(zone))
        return Take5TablePage(rows=table.rows, areas=table.areas, bands=table.bands)

    @router.get(
        "/api/take5-table.csv",
        response_class=Response,
        responses={
            200: {"content": {"text/csv": {}}, "description": "The rows as CSV"},
            **_UNREADABLE,
        },
    )
    def take5_table_csv(
        zone: ZoneName,
        filters: Annotated[Take5Filters, Depends(_filters)],
    ) -> Response:
        """Export the same rows as CSV, to open in a spreadsheet (E5).

        Args:
            zone: The page's time zone.
            filters: What to narrow the table to.
        """
        today: date = datetime.now(ZoneInfo(zone)).date()
        # The byte-order mark lets Excel read the CSV's apostrophes and dashes.
        return Response(
            content="﻿" + service.csv(filters, ZoneInfo(zone)),
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="take5s-{today}.csv"',
            },
        )

    return router
