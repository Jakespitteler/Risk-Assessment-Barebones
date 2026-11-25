"""Lay every saved Take 5 out as a filtered table, for the page and CSV (E1 to E6)."""

from datetime import UTC, datetime, tzinfo
from typing import ClassVar

from pydantic import BaseModel, ConfigDict

from risk_assessment.domain.take5.areas import risk_by_area
from risk_assessment.domain.take5.saved import SavedTake5
from risk_assessment.domain.take5.table import (
    Take5Filters,
    Take5Row,
    column_values,
    matches,
    table_csv,
    table_rows,
)
from risk_assessment.domain.take5.template import Take5Template
from risk_assessment.services.ports import Take5Repository

# Earlier than any Take 5, so every saved one is laid out (as D118 ranks them all).
_EVERY_TAKE5: datetime = datetime.min.replace(tzinfo=UTC)


class Take5Table(BaseModel):
    """The rows let through, and the values each column's filter can tick.

    Attributes:
        rows: The rows, the most important first (E2).
        areas: Every area with a Take 5, by the spelling typed most (A1).
        bands: The card's risk bands, lowest first.
        jobs: Every job, each once, A to Z (E6).
        workers: Every worker, each once, A to Z (E6).
        importances: Every importance, highest first (E6).
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    rows: tuple[Take5Row, ...]
    areas: tuple[str, ...]
    bands: tuple[str, ...]
    jobs: tuple[str, ...]
    workers: tuple[str, ...]
    importances: tuple[int, ...]


class Take5TableService:
    """Lays out every saved Take 5, by the rules the app already has. Saves nothing."""

    def __init__(self, repository: Take5Repository, template: Take5Template) -> None:
        """Set up the table.

        Args:
            repository: Where the Take 5s are kept.
            template: The card, for its questions and risk bands.
        """
        self._repository: Take5Repository = repository
        self._template: Take5Template = template

    def table(self, filters: Take5Filters, zone: tzinfo) -> Take5Table:
        """Lay out and filter every saved Take 5 (E1 to E4, E6).

        Args:
            filters: What to narrow the table to.
            zone: The zone of whoever asked, for a Take 5 with no start time.

        Returns:
            The rows, and what each filter can choose from.
        """
        take5s: tuple[SavedTake5, ...] = self._repository.list_saved_since(_EVERY_TAKE5)
        every_row: tuple[Take5Row, ...] = table_rows(take5s, Take5Filters(), zone)
        return Take5Table(
            rows=tuple(row for row in every_row if matches(row, filters)),
            areas=tuple(
                sorted(
                    (area.name for area in risk_by_area(take5s)),
                    key=str.casefold,
                ),
            ),
            bands=self.bands,
            jobs=column_values(row.job for row in every_row),
            workers=column_values(row.worker_name for row in every_row),
            importances=tuple(
                sorted({row.importance for row in every_row}, reverse=True),
            ),
        )

    def csv(self, filters: Take5Filters, zone: tzinfo) -> str:
        """Write the filtered table as CSV (E5).

        Args:
            filters: What to narrow the table to.
            zone: The zone of whoever asked.

        Returns:
            The CSV.
        """
        return table_csv(self.table(filters, zone).rows, self._template)

    @property
    def bands(self) -> tuple[str, ...]:
        """The card's risk bands, lowest first, each once."""
        cells = sorted(
            (cell for row in self._template.matrix.cells for cell in row),
            key=lambda cell: cell.score,
        )
        return tuple(dict.fromkeys(cell.band for cell in cells))
