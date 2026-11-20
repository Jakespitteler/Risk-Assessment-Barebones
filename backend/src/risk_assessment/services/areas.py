"""Group the last 30 days of Take 5s by where the job is, hottest first (A1 to A5)."""

from datetime import datetime

from risk_assessment.domain.take5.areas import AreaRisk, area_since, risk_by_area
from risk_assessment.domain.take5.saved import SavedTake5
from risk_assessment.services.ports import Take5Repository


class AreaRiskService:
    """Works out risk by area from saved Take 5s. Nothing is saved or sent to an AI."""

    def __init__(self, repository: Take5Repository) -> None:
        """Take the storage from the composition root.

        Args:
            repository: Where the Take 5s are kept.
        """
        self._repository: Take5Repository = repository

    def last_30_days(self, midnight_today: datetime) -> tuple[AreaRisk, ...]:
        """Group the Take 5s started in the last 30 days, today included (A2).

        A Take 5 counts from when it was started, or when it was saved if it has no
        start time, finished or not, as today's review counts them (W7).

        Args:
            midnight_today: Midnight today where the phone is, with its time zone.

        Returns:
            Each area, hottest first.
        """
        earliest: datetime = area_since(midnight_today)
        take5s: tuple[SavedTake5, ...] = tuple(
            take5
            for take5 in self._repository.list_saved_since(earliest)
            if (take5.started_at or take5.created_at) >= earliest
        )
        return risk_by_area(take5s)
