"""Every saved Take 5 as a row of a table, filtered and written as CSV (spec E1 to E5).

Each value comes from rules the app already has: the ranking's importance, line and
thought gaps (W1 to W5, W10, P4), the area (A1) and the verdict (V1 to V3). Nothing
here decides anything new about a Take 5; it only lays the values out.
"""

import csv
import io
from collections.abc import Sequence
from datetime import date, datetime, tzinfo
from typing import ClassVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from risk_assessment.domain.controls import Control
from risk_assessment.domain.risk import RiskRating
from risk_assessment.domain.take5.areas import area_key
from risk_assessment.domain.take5.ranking import (
    RUSHED_GAP,
    highest_risk,
    minutes_taken,
    rule_line,
    thought_gaps,
    worst_score,
)
from risk_assessment.domain.take5.saved import SavedTake5
from risk_assessment.domain.take5.template import Take5Template

GOOD_TO_GO: str = "Good to go"
DONT_START_YET: str = "Don't start yet"
NOT_FINISHED: str = "Not finished"
VERDICTS: tuple[str, ...] = (GOOD_TO_GO, DONT_START_YET, NOT_FINISHED)
WEEKDAYS: tuple[str, ...] = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)
# Four 6-hour blocks of the clock where a Take 5 was started (E3, from task 0039).
TIMES_OF_DAY: tuple[str, ...] = (
    "Midnight to 6 am",
    "6 am to noon",
    "Noon to 6 pm",
    "6 pm to midnight",
)
_HOURS_PER_BLOCK: int = 6
NO_GAPS: str = "No gaps"
SOME_GAPS: str = "Some gaps"
RUSHED: str = "Rushed"
# The choices of the thought gaps column's filter (E6).
THOUGHT_GAP_CHOICES: tuple[str, ...] = (NO_GAPS, SOME_GAPS, RUSHED)
# A cell a spreadsheet would run as a formula starts with one of these (E5).
_FORMULA_STARTS: tuple[str, ...] = ("=", "+", "-", "@", "\t", "\r")


class Take5Row(BaseModel):
    """One saved Take 5 laid out as a row (E1).

    Attributes:
        id: The Take 5's ID, to open it.
        started_at: When it was started, on the clock E3 reads it by: in the
            asker's zone, or a paper card's date as written (P5). None when not known.
        saved_at: When it was saved, in the asker's zone.
        started_on: The day it was started, or saved when the start isn't known, by
            the same clock as the month and weekday.
        month: Such as "2026-11".
        weekday: Such as "Monday".
        time_of_day: One of `TIMES_OF_DAY`, or None for a paper card with no time.
        worker_name: Who did it.
        job: What the job is.
        location: Where the job is, as typed.
        verdict: One of `VERDICTS`.
        importance: The ranking's worst score (W1): the highest risk before controls
            plus points for each thought gap.
        highest_score: The highest score before controls, or None when unrated.
        highest_band: That score's band, or None.
        needs_jha: True when that score needs a JHA on its card (R3, A3).
        why: The fixed rules' line for it (W1).
        thought_gaps: Each sign of little thought (W2 to W5, W10, P4).
        rushed: True when it was filled in in under 2 minutes (W5).
        minutes_taken: The minutes it took, or None when not known.
        hazard_count: How many hazards it has.
        control_count: How many controls, over every hazard.
        strong_control: True when any control is a strong kind (T3).
        answers: Each question's answer, by question ID; a blank is left out.
        from_paper: True when it was photographed off a paper card (P6).
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    id: UUID
    started_at: datetime | None
    saved_at: datetime
    started_on: date
    month: str
    weekday: str
    time_of_day: str | None
    worker_name: str
    job: str
    location: str
    verdict: str
    importance: int
    highest_score: int | None
    highest_band: str | None
    needs_jha: bool
    why: str
    thought_gaps: tuple[str, ...]
    rushed: bool
    minutes_taken: int | None
    hazard_count: int
    control_count: int
    strong_control: bool
    answers: dict[str, str]
    from_paper: bool


class Take5Filters(BaseModel):
    """What to narrow the table to (E4). Each empty filter lets every row through.

    Attributes:
        search: Words to find, each in the job, location or worker, ignoring capitals.
        start: The first day to show, by `Take5Row.started_on`.
        end: The last day to show.
        verdict: One of `VERDICTS`.
        band: A risk band, such as "Extreme".
        area: An area, matched as A1 matches, ignoring capitals and punctuation.
        weekday: One of `WEEKDAYS`.
        time_of_day: One of `TIMES_OF_DAY`.
        from_paper: True for paper cards only, False for none.
        job: Words to find, each in the job, ignoring capitals (E6).
        worker: Words to find, each in the worker's name, ignoring capitals (E6).
        min_importance: The lowest importance to show (E6).
        thought_gaps: One of `THOUGHT_GAP_CHOICES` (E6).
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    search: str = ""
    start: date | None = None
    end: date | None = None
    verdict: str | None = None
    band: str | None = None
    area: str | None = None
    weekday: str | None = None
    time_of_day: str | None = None
    from_paper: bool | None = None
    job: str = ""
    worker: str = ""
    min_importance: int | None = None
    thought_gaps: str | None = None


def take5_row(take5: SavedTake5, zone: tzinfo) -> Take5Row:
    """Lay one saved Take 5 out as a row (E1 to E3).

    Args:
        take5: A saved Take 5.
        zone: The zone of whoever asked, for a Take 5 with no start time.

    Returns:
        Its row.
    """
    when: datetime = _clock(take5, zone)
    riskiest: RiskRating | None = highest_risk(take5)
    gaps: tuple[str, ...] = thought_gaps(take5)
    controls: list[Control] = [
        control for hazard in take5.hazards for control in hazard.controls
    ]
    return Take5Row(
        id=take5.id,
        started_at=when if take5.started_at is not None else None,
        saved_at=take5.created_at.astimezone(zone),
        started_on=when.date(),
        month=f"{when.year:04d}-{when.month:02d}",
        weekday=WEEKDAYS[when.weekday()],
        time_of_day=_time_of_day(take5, when),
        worker_name=take5.worker_name,
        job=take5.job,
        location=take5.location,
        verdict=_verdict(take5),
        importance=worst_score(take5),
        highest_score=riskiest.score if riskiest is not None else None,
        highest_band=riskiest.band if riskiest is not None else None,
        needs_jha=riskiest is not None
        and take5.template.matrix.needs_jha(riskiest.score),
        why=rule_line(take5),
        thought_gaps=gaps,
        rushed=RUSHED_GAP in gaps,
        minutes_taken=minutes_taken(take5),
        hazard_count=len(take5.hazards),
        control_count=len(controls),
        strong_control=any(
            control.kind is not None and control.kind.is_strong for control in controls
        ),
        answers={
            question_id: answer.value for question_id, answer in take5.answers.items()
        },
        from_paper=take5.from_paper,
    )


def _clock(take5: SavedTake5, zone: tzinfo) -> datetime:
    """When a Take 5 was started, on the clock its time of day is read from (E3).

    A paper card keeps the date and time written on it, at the checker's offset (P5).
    A phone sends its start time in UTC, so it is read in the zone of whoever asks,
    standing in for the phone's. One with no start time goes by when it was saved.

    Args:
        take5: A saved Take 5.
        zone: The zone of whoever asked.

    Returns:
        The moment, on that clock.
    """
    if take5.started_at is None:
        return take5.created_at.astimezone(zone)
    if take5.from_paper:
        return take5.started_at
    return take5.started_at.astimezone(zone)


def matches(row: Take5Row, filters: Take5Filters) -> bool:
    """Say whether a row is let through by every filter (E4, E6).

    Args:
        row: A row of the table.
        filters: What to narrow the table to.

    Returns:
        True when the row passes them all.
    """
    found_in: str = f"{row.job}\n{row.location}\n{row.worker_name}".casefold()
    area: str = area_key(filters.area or "")
    checks: tuple[bool, ...] = (
        all(word in found_in for word in filters.search.casefold().split()),
        filters.start is None or row.started_on >= filters.start,
        filters.end is None or row.started_on <= filters.end,
        filters.verdict is None or row.verdict == filters.verdict,
        filters.band is None or row.highest_band == filters.band,
        not area or area_key(row.location) == area,
        filters.weekday is None or row.weekday == filters.weekday,
        filters.time_of_day is None or row.time_of_day == filters.time_of_day,
        filters.from_paper is None or row.from_paper == filters.from_paper,
        _has_words(row.job, filters.job),
        _has_words(row.worker_name, filters.worker),
        filters.min_importance is None or row.importance >= filters.min_importance,
        _has_thought_gaps(row, filters.thought_gaps),
    )
    return all(checks)


def _has_words(text: str, words: str) -> bool:
    """Say whether every word searched is in a text, ignoring capitals (E6).

    Args:
        text: A row's value, such as its job.
        words: The words to find; none finds every text.

    Returns:
        True when each word is found.
    """
    return all(word in text.casefold() for word in words.casefold().split())


def _has_thought_gaps(row: Take5Row, choice: str | None) -> bool:
    """Say whether a row's thought gaps match the column's filter (E6).

    Args:
        row: A row of the table.
        choice: One of `THOUGHT_GAP_CHOICES`, or None for every row.

    Returns:
        True when the row matches.
    """
    if choice is None:
        return True
    if choice == NO_GAPS:
        return not row.thought_gaps
    if choice == SOME_GAPS:
        return bool(row.thought_gaps)
    return choice == RUSHED and row.rushed


def table_rows(
    take5s: Sequence[SavedTake5],
    filters: Take5Filters,
    zone: tzinfo,
) -> tuple[Take5Row, ...]:
    """Lay out and filter Take 5s, the most important first, then the newest (E2).

    Args:
        take5s: The saved Take 5s.
        filters: What to narrow the table to.
        zone: The zone of whoever asked.

    Returns:
        The rows let through.
    """
    rows: list[Take5Row] = [take5_row(take5, zone) for take5 in take5s]
    kept: list[Take5Row] = [row for row in rows if matches(row, filters)]
    newest_first: list[Take5Row] = sorted(
        kept,
        key=lambda row: row.saved_at,
        reverse=True,
    )
    return tuple(sorted(newest_first, key=lambda row: row.importance, reverse=True))


def table_csv(rows: Sequence[Take5Row], template: Take5Template) -> str:
    """Write rows as CSV, one column per value and per question on the card (E5).

    A cell that starts like a spreadsheet formula gets an apostrophe in front, so a
    typed job is never run as one.

    Args:
        rows: The rows to write.
        template: The card, for the questions' words as headers.

    Returns:
        The CSV, with a header row.
    """
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\r\n")
    writer.writerow(
        [
            "Started",
            "Saved",
            "Month",
            "Weekday",
            "Time of day",
            "Worker",
            "Job",
            "Location",
            "Verdict",
            "Importance",
            "Highest risk",
            "Risk band",
            "Needs a JHA",
            "Why",
            "Thought gaps (count)",
            "Thought gaps",
            "Rushed",
            "Minutes taken",
            "Hazards",
            "Controls",
            "Strong control",
            "From paper",
            *(question.text for question in template.questions),
            "ID",
        ],
    )
    for row in rows:
        writer.writerow(
            [
                _safe(cell)
                for cell in (
                    row.started_at.isoformat() if row.started_at else "",
                    row.saved_at.isoformat(),
                    row.month,
                    row.weekday,
                    row.time_of_day or "",
                    row.worker_name,
                    row.job,
                    row.location,
                    row.verdict,
                    str(row.importance),
                    "" if row.highest_score is None else str(row.highest_score),
                    row.highest_band or "",
                    _yes_no(row.needs_jha),
                    row.why,
                    str(len(row.thought_gaps)),
                    "; ".join(row.thought_gaps),
                    _yes_no(row.rushed),
                    "" if row.minutes_taken is None else str(row.minutes_taken),
                    str(row.hazard_count),
                    str(row.control_count),
                    _yes_no(row.strong_control),
                    _yes_no(row.from_paper),
                    *(
                        row.answers.get(question.id, "")
                        for question in template.questions
                    ),
                    str(row.id),
                )
            ],
        )
    return out.getvalue()


def _verdict(take5: SavedTake5) -> str:
    """Name a Take 5's verdict.

    Args:
        take5: A saved Take 5.

    Returns:
        One of `VERDICTS`.
    """
    if take5.verdict is None:
        return NOT_FINISHED
    return GOOD_TO_GO if take5.verdict.can_start else DONT_START_YET


def _time_of_day(take5: SavedTake5, when: datetime) -> str | None:
    """Put the clock time a Take 5 was started into one of four 6-hour blocks (E3).

    Args:
        take5: A saved Take 5.
        when: When it was started, or saved, by its own clock.

    Returns:
        The block, or None for a paper card with a date and no time, which is saved
        as the start of that day (P5).
    """
    if (
        take5.from_paper
        and take5.started_at is not None
        and (when.hour, when.minute) == (0, 0)
    ):
        return None
    return TIMES_OF_DAY[when.hour // _HOURS_PER_BLOCK]


def _yes_no(value: bool) -> str:  # noqa: FBT001 - a value to write, not a switch
    """Write a yes or no for the CSV.

    Args:
        value: The value.

    Returns:
        "Yes" or "No".
    """
    return "Yes" if value else "No"


def _safe(cell: str) -> str:
    """Stop a spreadsheet from running a cell as a formula (E5).

    Args:
        cell: The cell's text.

    Returns:
        The text, with an apostrophe in front when it starts like a formula.
    """
    return f"'{cell}" if cell.startswith(_FORMULA_STARTS) else cell
