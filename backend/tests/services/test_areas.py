"""Tests for the risk-by-area service (spec A2), with Take 5s kept in memory."""

from datetime import datetime, timedelta, timezone

from risk_assessment.domain.take5.areas import AreaRisk
from risk_assessment.domain.take5.saved import SavedTake5
from risk_assessment.services.areas import AreaRiskService
from tests.domain.take5.test_areas import WORKSHOP, area_take5
from tests.services.test_take5s import MemoryRepository

PERTH = timezone(timedelta(hours=8))
MIDNIGHT_TODAY: datetime = datetime(2026, 11, 21, tzinfo=PERTH)


def _started_at(started: datetime, location: str) -> SavedTake5:
    """Make a careful Take 5 started at a moment and saved 10 minutes later.

    Args:
        started: When it was started.
        location: Where the job is.

    Returns:
        The saved Take 5.
    """
    return area_take5(location).model_copy(
        update={"started_at": started, "created_at": started + timedelta(minutes=10)},
    )


def test_example_129_a_take5_started_before_the_30_days_is_left_out() -> None:
    """A2: midnight 29 days ago counts; a minute before it doesn't."""
    repository = MemoryRepository()
    first_day: datetime = MIDNIGHT_TODAY - timedelta(days=29)
    repository.add(_started_at(first_day, WORKSHOP))
    repository.add(_started_at(first_day - timedelta(minutes=1), "Crusher"))

    areas: tuple[AreaRisk, ...] = AreaRiskService(repository).last_30_days(
        MIDNIGHT_TODAY,
    )

    assert [area.name for area in areas] == [WORKSHOP]
