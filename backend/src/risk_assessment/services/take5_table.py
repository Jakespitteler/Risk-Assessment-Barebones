"""Lay every saved Take 5 out as a filtered table, for the page and CSV (E1 to E5)."""

from datetime import UTC, datetime, tzinfo
from typing import ClassVar

from pydantic import BaseModel, ConfigDict

from risk_assessment.domain.take5.areas import risk_by_area
from risk_assessment.domain.take5.saved import SavedTake5
from risk_assessment.domain.take5.table import (
    Take5Filters,
    Take5Row,
    table_csv,
    table_rows,
)
from risk_assessment.domain.take5.template import Take5Template
from risk_assessment.services.ports import Take5Repository

# Earlier than any Take 5, so every saved one is laid out (as D118 ranks them all).
_EVERY_TAKE5: datetime = datetime.min.replace(tzinfo=UTC)


class Take5Table(BaseModel):
    """The rows let through, and the areas a person can filter by.

    Attributes:
        rows: The rows, the most important first (E2).
        areas: Every area with a Take 5, by the spelling typed most (A1).
        bands: The card's risk bands, lowest first.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    rows: tuple[Take5Row, ...]
    areas: tuple[str, ...]
    bands: tuple[str, ...]


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
        """Lay out and filter every saved Take 5 (E1 to E4).

        Args:
            filters: What to narrow the table to.
            zone: The zone of whoever asked, for a Take 5 with no start time.

        Returns:
            The rows, and what each filter can choose from.
        """
        take5s: tuple[SavedTake5, ...] = self._repository.list_saved_since(_EVERY_TAKE5)
        return Take5Table(
            rows=table_rows(take5s, filters, zone),
            areas=tuple(sorted(area.name for area in risk_by_area(take5s))),
            bands=self.bands,
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
