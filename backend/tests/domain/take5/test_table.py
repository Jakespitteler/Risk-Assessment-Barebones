"""Tests for the table of saved Take 5s and its CSV (spec E1 to E5), from examples."""

import csv
import io
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from risk_assessment.domain.take5.saved import SavedTake5
from risk_assessment.domain.take5.table import (
    DONT_START_YET,
    GOOD_TO_GO,
    NOT_FINISHED,
    Take5Filters,
    Take5Row,
    matches,
    table_csv,
    table_rows,
    take5_row,
)
from risk_assessment.domain.take5.template import BOOKLET_TEMPLATE
from risk_assessment.domain.take5.verdict import Verdict
from tests.domain.take5.test_ranking import ranked_take5

PERTH = ZoneInfo("Australia/Perth")
# Saturday 21 Nov 2026, 7 am in Perth.
SATURDAY_MORNING: datetime = datetime(2026, 11, 21, 7, 0, tzinfo=PERTH)


def started(when: datetime, take5: SavedTake5 | None = None) -> SavedTake5:
    """Make the careful Take 5 started at a moment and saved 10 minutes later.

    Args:
        when: When it was started, with its zone.
        take5: The Take 5 to move, or the careful one.

    Returns:
        The Take 5.
    """
    return (take5 or ranked_take5()).model_copy(
        update={"started_at": when, "created_at": when + timedelta(minutes=10)},
    )


def row(take5: SavedTake5) -> Take5Row:
    """Lay one Take 5 out as a row, asked from Perth.

    Args:
        take5: A saved Take 5.

    Returns:
        Its row.
    """
    return take5_row(take5, PERTH)


def test_example_141_the_careful_one_as_a_row() -> None:
    """Its time, verdict, importance and band, from the existing rules (E1 to E3)."""
    careful: Take5Row = row(started(SATURDAY_MORNING))

    assert (careful.month, careful.weekday, careful.time_of_day) == (
        "2026-11",
        "Saturday",
        "6 am to noon",
    )
    assert careful.verdict == GOOD_TO_GO
    assert (careful.importance, careful.highest_score, careful.highest_band) == (
        8,
        8,
        "Moderate",
    )
    assert not careful.needs_jha
    assert careful.why == "Highest risk 8 Moderate. No signs of a rushed Take 5."
    assert careful.thought_gaps == ()
    assert not careful.rushed
    assert careful.minutes_taken == 10
    assert (careful.hazard_count, careful.control_count) == (1, 1)
    assert careful.strong_control
    assert careful.worker_name == "Sam Example"
    assert not careful.from_paper


def test_example_142_the_most_important_comes_first() -> None:
    """Importance is the ranking's worst score, highest first (E2)."""
    high: SavedTake5 = started(
        SATURDAY_MORNING,
        ranked_take5(before=("Possible", "Major")),
    )
    gap: SavedTake5 = started(
        SATURDAY_MORNING,
        ranked_take5(description="Moving wheel"),
    )

    rows: tuple[Take5Row, ...] = table_rows([gap, high], Take5Filters(), PERTH)

    assert [each.importance for each in rows] == [18, 13]
    assert rows[0].needs_jha


def test_example_143_a_minute_before_and_at_midnight() -> None:
    """The four blocks meet at midnight, and the weekday turns there (E3)."""
    late: Take5Row = row(started(datetime(2026, 11, 21, 23, 59, tzinfo=PERTH)))
    midnight: Take5Row = row(started(datetime(2026, 11, 22, 0, 0, tzinfo=PERTH)))

    assert (late.weekday, late.time_of_day) == ("Saturday", "6 pm to midnight")
    assert (midnight.weekday, midnight.time_of_day) == ("Sunday", "Midnight to 6 am")


def test_example_144_a_paper_card_with_no_time_has_no_time_of_day() -> None:
    """A date alone is saved as the start of the day, which isn't a time (E3, P5)."""
    card: SavedTake5 = started(datetime(2026, 4, 3, tzinfo=PERTH)).model_copy(
        update={"from_paper": True},
    )

    paper: Take5Row = row(card)

    assert (paper.month, paper.weekday, paper.time_of_day) == (
        "2026-04",
        "Friday",
        None,
    )
    assert paper.from_paper


def test_example_145_no_start_time_goes_by_the_save_in_the_askers_zone() -> None:
    """11 pm UTC on 20 Nov is 7 am on Saturday 21 Nov in Perth (E3)."""
    old: SavedTake5 = ranked_take5(
        minutes_taken=None,
        saved_at=datetime(2026, 11, 20, 23, 0, tzinfo=UTC),
    )

    saved: Take5Row = row(old)

    assert saved.started_at is None
    assert (saved.started_on, saved.weekday, saved.time_of_day) == (
        date(2026, 11, 21),
        "Saturday",
        "6 am to noon",
    )


def test_example_146_words_are_found_ignoring_capitals() -> None:
    """The search looks in the job, location and worker (E4)."""
    careful: Take5Row = row(started(SATURDAY_MORNING))

    assert matches(careful, Take5Filters(search="TYRE"))
    assert matches(careful, Take5Filters(search="sam ex"))
    assert not matches(careful, Take5Filters(search="crusher"))


def test_example_147_a_date_range_keeps_both_ends() -> None:
    """From 21 Nov to 21 Nov keeps only that day (E4)."""
    days: list[SavedTake5] = [
        started(SATURDAY_MORNING + timedelta(days=offset)) for offset in (-1, 0, 1)
    ]
    one_day = Take5Filters(start=date(2026, 11, 21), end=date(2026, 11, 21))

    rows: tuple[Take5Row, ...] = table_rows(days, one_day, PERTH)

    assert [each.started_on for each in rows] == [date(2026, 11, 21)]


def test_example_148_an_area_matches_as_risk_by_area_does() -> None:
    """Capitals, spaces and punctuation are ignored (E4, A1)."""
    workshop: Take5Row = row(
        started(SATURDAY_MORNING).model_copy(
            update={"location": "Light vehicle workshop"},
        ),
    )

    assert matches(workshop, Take5Filters(area="light-vehicle  workshop."))
    assert not matches(workshop, Take5Filters(area="Crusher"))


def test_example_149_a_cell_like_a_formula_is_never_run() -> None:
    """A spreadsheet would run "=…", so it gets an apostrophe (E5)."""
    formula: SavedTake5 = started(SATURDAY_MORNING).model_copy(
        update={"job": '=HYPERLINK("http://example.com")'},
    )

    exported: str = table_csv([row(formula)], BOOKLET_TEMPLATE)
    cells: list[list[str]] = list(csv.reader(io.StringIO(exported)))

    assert cells[1][cells[0].index("Job")] == '\'=HYPERLINK("http://example.com")'


def test_example_150_the_careful_one_exported() -> None:
    """A header, then a row with its values and each question's answer (E5)."""
    careful: SavedTake5 = started(SATURDAY_MORNING)

    exported: str = table_csv([row(careful)], BOOKLET_TEMPLATE)
    header, values = list(csv.reader(io.StringIO(exported)))
    cell: dict[str, str] = dict(zip(header, values, strict=True))

    assert cell["Started"] == "2026-11-21T07:00:00+08:00"
    assert cell["Weekday"] == "Saturday"
    assert cell["Verdict"] == GOOD_TO_GO
    assert (cell["Importance"], cell["Risk band"], cell["Needs a JHA"]) == (
        "8",
        "Moderate",
        "No",
    )
    assert cell["Worker"] == "Sam Example"
    assert cell[BOOKLET_TEMPLATE.questions[0].text] == "Yes"
    assert cell["ID"] == str(careful.id)
    assert len(header) == 23 + len(BOOKLET_TEMPLATE.questions)


@pytest.mark.parametrize(
    ("verdict", "answer", "named"),
    [
        (Verdict(can_start=True, reasons=()), "Done", GOOD_TO_GO),
        (
            Verdict(can_start=False, reasons=("Talk to your supervisor.",)),
            "Done",
            DONT_START_YET,
        ),
        (None, None, NOT_FINISHED),
    ],
)
def test_each_verdict_is_named_and_can_be_filtered(
    verdict: Verdict | None,
    answer: str | None,
    named: str,
) -> None:
    """An unfinished Take 5 counts too, as "Not finished" (E1, E4)."""
    take5: SavedTake5 = started(
        SATURDAY_MORNING,
        ranked_take5(answer=answer),
    ).model_copy(
        update={"verdict": verdict},
    )

    laid_out: Take5Row = row(take5)

    assert laid_out.verdict == named
    assert matches(laid_out, Take5Filters(verdict=named))


def test_the_other_filters_keep_only_matching_rows() -> None:
    """Band, weekday, time of day and from paper each narrow the rows (E4)."""
    careful: Take5Row = row(started(SATURDAY_MORNING))

    assert matches(careful, Take5Filters(band="Moderate", weekday="Saturday"))
    assert not matches(careful, Take5Filters(band="Extreme"))
    assert not matches(careful, Take5Filters(time_of_day="Noon to 6 pm"))
    assert not matches(careful, Take5Filters(from_paper=True))
    assert matches(careful, Take5Filters(from_paper=False))


def test_a_rushed_take5_is_marked_and_counts_its_gap() -> None:
    """Under 2 minutes is rushed (E1, W5)."""
    rushed: Take5Row = row(ranked_take5(minutes_taken=1))

    assert rushed.rushed
    assert rushed.importance == 13
