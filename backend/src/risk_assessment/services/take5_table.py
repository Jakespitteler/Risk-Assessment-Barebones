"""Lay every saved Take 5 out as a filtered table, for the page and CSV (E1 to E6)."""

from datetime import UTC, datetime, tzinfo
from typing import ClassVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from risk_assessment.domain.take5.areas import risk_by_area
from risk_assessment.domain.take5.saved import SavedTake5
from risk_assessment.domain.take5.table import (
    VERDICTS,
    Take5Filters,
    Take5Row,
    column_values,
    left_by_other_filters,
    matches,
    table_csv,
    table_rows,
    thought_gap_choices,
)
from risk_assessment.domain.take5.template import Take5Template
from risk_assessment.services.ports import Take5Repository

# Earlier than any Take 5, so every saved one is laid out (as D118 ranks them all).
_EVERY_TAKE5: datetime = datetime.min.replace(tzinfo=UTC)


class Take5Table(BaseModel):
    """The rows let through, and the values each column's filter can tick.

    Each column lists only the values of the rows the other filters keep (E6).

    Attributes:
        rows: The rows, the most important first (E2).
        verdicts: The verdicts, in the order of `VERDICTS`.
        areas: The areas, by the spelling typed most (A1), A to Z.
        bands: The risk bands, lowest first.
        thought_gap_choices: The thought gaps choices some row matches.
        jobs: The jobs, each once, A to Z.
        workers: The workers, each once, A to Z.
        importances: The importances, highest first.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    rows: tuple[Take5Row, ...]
    verdicts: tuple[str, ...]
    thought_gap_choices: tuple[str, ...]
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

        def left(column: str) -> tuple[Take5Row, ...]:
            """Keep the rows every filter but this column's own lets through."""
            return left_by_other_filters(every_row, filters, column)

        area_ids: set[UUID] = {row.id for row in left("area")}
        verdicts: set[str] = {row.verdict for row in left("verdict")}
        bands: set[str | None] = {row.highest_band for row in left("band")}
        return Take5Table(
            rows=tuple(row for row in every_row if matches(row, filters)),
            verdicts=tuple(verdict for verdict in VERDICTS if verdict in verdicts),
            thought_gap_choices=thought_gap_choices(left("thought_gaps")),
            areas=tuple(
                sorted(
                    (
                        area.name
                        for area in risk_by_area(
                            [take5 for take5 in take5s if take5.id in area_ids],
                        )
                    ),
                    key=str.casefold,
                ),
            ),
            bands=tuple(band for band in self.bands if band in bands),
            jobs=column_values(row.job for row in left("job")),
            workers=column_values(row.worker_name for row in left("worker")),
            importances=tuple(
                sorted({row.importance for row in left("importance")}, reverse=True),
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
