"""Find patterns over time in every saved Take 5 (S1 to S5)."""

from datetime import UTC, datetime, tzinfo

from risk_assessment.domain.take5.patterns import Patterns, patterns_over_time
from risk_assessment.domain.take5.saved import SavedTake5
from risk_assessment.domain.take5.table import Take5Filters, Take5Row, table_rows
from risk_assessment.domain.take5.template import Take5Template
from risk_assessment.services.ports import Take5Repository

# Earlier than any Take 5, so every saved one counts (S1).
_EVERY_TAKE5: datetime = datetime.min.replace(tzinfo=UTC)


class PatternsService:
    """Works out patterns over time from saved Take 5s. Saves nothing; uses no AI."""

    def __init__(self, repository: Take5Repository, template: Take5Template) -> None:
        """Take the storage and the card from the composition root.

        Args:
            repository: Where the Take 5s are kept.
            template: The card, for its hazard questions.
        """
        self._repository: Take5Repository = repository
        self._template: Take5Template = template

    def patterns(self, zone: tzinfo) -> Patterns:
        """Find the patterns in every saved Take 5, finished or not (S1).

        Args:
            zone: The zone of whoever asked, to read a phone's start time in (E3).

        Returns:
            The sentences and the counts by month, weekday and time of day.
        """
        take5s: tuple[SavedTake5, ...] = self._repository.list_saved_since(
            _EVERY_TAKE5,
        )
        rows: tuple[Take5Row, ...] = table_rows(take5s, Take5Filters(), zone)
        return patterns_over_time(rows, self._template.questions)
