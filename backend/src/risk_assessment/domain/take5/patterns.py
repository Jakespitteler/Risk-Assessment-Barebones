"""Patterns over time in saved Take 5s, as plain sentences and counts (spec S1 to S5).

Each saved Take 5 is first laid out as a table row (E1 to E3), so its month, weekday,
time of day, verdict and thought gaps come from the rules the app already has. This
module only compares groups of rows: no AI is used, and every number can be checked
by hand.
"""

import math
from collections.abc import Callable, Sequence
from datetime import date
from fractions import Fraction
from typing import ClassVar

from pydantic import BaseModel, ConfigDict

from risk_assessment.domain.questions import Answer, Question, QuestionRole
from risk_assessment.domain.take5.table import (
    DONT_START_YET,
    NOT_FINISHED,
    TIMES_OF_DAY,
    WEEKDAYS,
    Take5Row,
)

# A group, and all the other Take 5s it is compared with, each need this many (S4).
SMALLEST_GROUP: int = 5
# A sign must show up this many times in a group before it is worth a sentence (S4).
FEWEST_SIGNS: int = 3
# How many times as common in a group as elsewhere a sign must be (S4).
TIMES_AS_COMMON: int = 2
# The page shows at most this many sentences, the strongest first (S4).
MOST_SENTENCES: int = 5
# From this many times as common, the sentence rounds to a whole number (S4).
_WHOLE_TIMES_FROM: int = 10

_MONTH_NAMES: tuple[str, ...] = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)


class Sign(BaseModel):
    """Something a Take 5 can show, counted in each group (S3).

    Attributes:
        described: What a Take 5 with it did, to finish a sentence, such as
            "were rushed".
        counted: What the Take 5s it can apply to are called, such as
            "finished Take 5s".
        applies: Whether the sign can apply to a row at all; a row it can't is left
            out of both sides of the comparison.
        shown: Whether a row shows the sign.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    described: str
    counted: str
    applies: Callable[[Take5Row], bool]
    shown: Callable[[Take5Row], bool]


class Grouping(BaseModel):
    """One way to group Take 5s by time: by month, weekday or time of day (S2).

    Attributes:
        name: The grouping's name in the API, such as "weekday".
        group_of: The group a row is in, or None when it has none.
        in_words: How a group reads in a sentence, such as "on Mondays".
        elsewhere: How every other group reads, such as "on other days".
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    name: str
    group_of: Callable[[Take5Row], str | None]
    in_words: Callable[[str], str]
    elsewhere: str


class PatternSentence(BaseModel):
    """One pattern worth a sentence, with the numbers behind it (S4).

    Attributes:
        text: The sentence, such as "4 of 8 Take 5s on Mondays were rushed: 3 times
            the rate on other days (5 of 30)."
        table_filters: The All Take 5s table's filters that show the group's Take 5s,
            as the table's address names them, such as {"weekday": "Monday"}.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    text: str
    table_filters: dict[str, str]


class GroupCounts(BaseModel):
    """How many Take 5s in one group showed each of the main signs (S5).

    Attributes:
        group: The group's name, such as "November 2026", "Monday" or "6 am to noon".
        take5_count: How many Take 5s are in it.
        high_risk_count: How many needed a JHA before controls (A3).
        rushed_count: How many were filled in in under 2 minutes (W5).
        thought_gaps_count: How many have at least one thought gap.
        stopped_count: How many were told "Don't start yet".
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    group: str
    take5_count: int
    high_risk_count: int
    rushed_count: int
    thought_gaps_count: int
    stopped_count: int


class Patterns(BaseModel):
    """Patterns over time in every saved Take 5 (S1 to S5).

    Attributes:
        take5_count: How many saved Take 5s were looked at.
        sentences: The patterns worth a sentence, strongest first.
        by_month: The counts in each month with a Take 5, oldest first.
        by_weekday: The counts on each weekday, Monday first.
        by_time_of_day: The counts in each time of day, from midnight.
        no_time_of_day_count: How many paper cards have no time written on them, and
            so aren't counted by time of day.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    take5_count: int
    sentences: tuple[PatternSentence, ...]
    by_month: tuple[GroupCounts, ...]
    by_weekday: tuple[GroupCounts, ...]
    by_time_of_day: tuple[GroupCounts, ...]
    no_time_of_day_count: int


class _Comparison(BaseModel):
    """A sign's count in one group beside its count in all the others (S4).

    Attributes:
        grouping: How the Take 5s were grouped.
        group: The group.
        sign: The sign counted.
        in_group: How many Take 5s in the group the sign can apply to.
        shown_in_group: How many of those show it.
        elsewhere: How many Take 5s in other groups the sign can apply to.
        shown_elsewhere: How many of those show it.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    grouping: Grouping
    group: str
    sign: Sign
    in_group: int
    shown_in_group: int
    elsewhere: int
    shown_elsewhere: int


def month_name(month: str) -> str:
    """Name a table row's month in words.

    Args:
        month: Such as "2026-11".

    Returns:
        Such as "November 2026".
    """
    year, number = month.split("-")
    return f"{_MONTH_NAMES[int(number) - 1]} {year}"


def _time_of_day_words(time_of_day: str) -> str:
    """Put a time of day into a sentence.

    Args:
        time_of_day: One of `TIMES_OF_DAY`, such as "Midnight to 6 am".

    Returns:
        Such as "from midnight to 6 am".
    """
    return f"from {time_of_day[0].lower()}{time_of_day[1:]}"


BY_MONTH = Grouping(
    name="month",
    group_of=lambda row: row.month,
    in_words=lambda month: f"in {month_name(month)}",
    elsewhere="in other months",
)
BY_WEEKDAY = Grouping(
    name="weekday",
    group_of=lambda row: row.weekday,
    in_words=lambda weekday: f"on {weekday}s",
    elsewhere="on other days",
)
BY_TIME_OF_DAY = Grouping(
    name="time_of_day",
    group_of=lambda row: row.time_of_day,
    in_words=_time_of_day_words,
    elsewhere="at other times of day",
)
GROUPINGS: tuple[Grouping, ...] = (BY_MONTH, BY_WEEKDAY, BY_TIME_OF_DAY)

HIGH_RISK = Sign(
    described="were high risk",
    counted="Take 5s",
    applies=lambda _row: True,
    shown=lambda row: row.needs_jha,
)
RUSHED = Sign(
    described="were rushed",
    counted="timed Take 5s",
    applies=lambda row: row.minutes_taken is not None,
    shown=lambda row: row.rushed,
)
THOUGHT_GAPS = Sign(
    described="had thought gaps",
    counted="Take 5s",
    applies=lambda _row: True,
    shown=lambda row: bool(row.thought_gaps),
)
STOPPED = Sign(
    described="were told “Don’t start yet”",
    counted="finished Take 5s",
    applies=lambda row: row.verdict != NOT_FINISHED,
    shown=lambda row: row.verdict == DONT_START_YET,
)
MAIN_SIGNS: tuple[Sign, ...] = (HIGH_RISK, RUSHED, THOUGHT_GAPS, STOPPED)


def yes_to(question: Question) -> Sign:
    """Make the sign of a Yes to one hazard question, such as heights (S3).

    Args:
        question: A hazard question on the card.

    Returns:
        The sign; a blank answer counts as not Yes.
    """
    return Sign(
        described=f"answered Yes to “{question.text}”",
        counted="Take 5s",
        applies=lambda _row: True,
        shown=lambda row: row.answers.get(question.id) == Answer.YES,
    )


def signs_for(questions: Sequence[Question]) -> tuple[Sign, ...]:
    """List every sign counted: the main four, then a Yes to each hazard question (S3).

    Args:
        questions: The card's questions, in its order.

    Returns:
        The signs, in the order a tie between sentences goes by.
    """
    hazard_signs: tuple[Sign, ...] = tuple(
        yes_to(question)
        for question in questions
        if question.role is QuestionRole.HAZARD
    )
    return MAIN_SIGNS + hazard_signs


def groups_in_order(grouping: Grouping, rows: Sequence[Take5Row]) -> tuple[str, ...]:
    """List a grouping's groups: every weekday and time of day, and each month seen.

    Args:
        grouping: How the Take 5s are grouped.
        rows: The rows.

    Returns:
        The groups in time order: months oldest first, Monday first, from midnight.
    """
    if grouping is BY_WEEKDAY:
        return WEEKDAYS
    if grouping is BY_TIME_OF_DAY:
        return TIMES_OF_DAY
    return tuple(sorted({row.month for row in rows}))


def compare(
    rows: Sequence[Take5Row],
    grouping: Grouping,
    group: str,
    sign: Sign,
) -> _Comparison:
    """Count a sign in one group and in every other group (S4).

    A row with no group in this grouping, such as a paper card with no time written
    on it, is on neither side, nor is a row the sign can't apply to.

    Args:
        rows: The rows.
        grouping: How the Take 5s are grouped.
        group: The group to compare.
        sign: The sign to count.

    Returns:
        The two counts, side by side.
    """
    counted: list[Take5Row] = [
        row for row in rows if sign.applies(row) and grouping.group_of(row) is not None
    ]
    in_group: list[Take5Row] = [
        row for row in counted if grouping.group_of(row) == group
    ]
    elsewhere: list[Take5Row] = [
        row for row in counted if grouping.group_of(row) != group
    ]
    return _Comparison(
        grouping=grouping,
        group=group,
        sign=sign,
        in_group=len(in_group),
        shown_in_group=sum(1 for row in in_group if sign.shown(row)),
        elsewhere=len(elsewhere),
        shown_elsewhere=sum(1 for row in elsewhere if sign.shown(row)),
    )


def is_worth_a_sentence(comparison: _Comparison) -> bool:
    """Say whether a sign stands out enough in a group to be worth a sentence (S4).

    Both sides need at least `SMALLEST_GROUP` Take 5s, the sign must show up at least
    `FEWEST_SIGNS` times in the group, and its rate there must be at least
    `TIMES_AS_COMMON` times its rate elsewhere. The rates are compared by
    multiplying across, so no rounding can tip a pattern over the line.

    Args:
        comparison: The sign's counts in the group and elsewhere.

    Returns:
        True when it is worth a sentence.
    """
    return (
        comparison.in_group >= SMALLEST_GROUP
        and comparison.elsewhere >= SMALLEST_GROUP
        and comparison.shown_in_group >= FEWEST_SIGNS
        and comparison.shown_in_group * comparison.elsewhere
        >= TIMES_AS_COMMON * comparison.shown_elsewhere * comparison.in_group
    )


def times_as_common(comparison: _Comparison) -> Fraction | None:
    """Work out how many times as common a sign is in a group as elsewhere.

    It is an exact fraction, so two patterns as strong as each other tie, and the
    tie goes by S4's order rather than by a float's last digit.

    Args:
        comparison: The sign's counts in the group and elsewhere.

    Returns:
        The ratio of the two rates, or None when it never shows up elsewhere.
    """
    if comparison.shown_elsewhere == 0:
        return None
    return Fraction(
        comparison.shown_in_group * comparison.elsewhere,
        comparison.in_group * comparison.shown_elsewhere,
    )


def _strongest_first(comparison: _Comparison) -> tuple[Fraction | float, int]:
    """Give the key that sorts patterns strongest first (S4).

    Never seen elsewhere is the strongest; then the most times as common, then the
    sign seen most often in its group. Any tie left keeps the order it was found in.

    Args:
        comparison: A sign's counts in a group and elsewhere.

    Returns:
        The key, smallest for the strongest.
    """
    ratio: Fraction | None = times_as_common(comparison)
    return (
        -ratio if ratio is not None else -math.inf,
        -comparison.shown_in_group,
    )


def _times_in_words(ratio: Fraction) -> str:
    """Say a ratio in words: to one decimal place under 10, else a whole number.

    A half rounds up, as a person checking by hand would (as W9's minutes do).

    Args:
        ratio: How many times as common, 2 or more.

    Returns:
        Such as "twice", "3 times", "2.5 times" or "29 times".
    """
    half: Fraction = Fraction(1, 2)
    tenths: int = (
        math.floor(ratio + half) * 10
        if ratio >= _WHOLE_TIMES_FROM
        else math.floor(ratio * 10 + half)
    )
    if tenths == TIMES_AS_COMMON * 10:
        return "twice"
    whole, tenth = divmod(tenths, 10)
    return f"{whole} times" if tenth == 0 else f"{whole}.{tenth} times"


def sentence_text(comparison: _Comparison) -> str:
    """Write a pattern as one plain sentence with its numbers (S4).

    Args:
        comparison: A sign's counts in a group and elsewhere, worth a sentence.

    Returns:
        Such as "4 of 8 Take 5s on Mondays were rushed: 3 times the rate on other days
        (5 of 30)."
    """
    grouping: Grouping = comparison.grouping
    found: str = (
        f"{comparison.shown_in_group} of {comparison.in_group} "
        f"{comparison.sign.counted} {grouping.in_words(comparison.group)} "
        f"{comparison.sign.described}"
    )
    ratio: Fraction | None = times_as_common(comparison)
    if ratio is None:
        return f"{found}, and none of {comparison.elsewhere} {grouping.elsewhere}."
    return (
        f"{found}: {_times_in_words(ratio)} the rate "
        f"{grouping.elsewhere} "
        f"({comparison.shown_elsewhere} of {comparison.elsewhere})."
    )


def table_filters(grouping: Grouping, group: str) -> dict[str, str]:
    """Name the All Take 5s table's filters that show one group's Take 5s (E4).

    Args:
        grouping: How the Take 5s are grouped.
        group: The group, such as "2026-11" or "Monday".

    Returns:
        The filters, as the table's address names them; a month is a date range.
    """
    if grouping is not BY_MONTH:
        return {grouping.name: group}
    year, number = (int(part) for part in group.split("-"))
    first_day: date = date(year, number, 1)
    next_month: date = date(year + number // 12, number % 12 + 1, 1)
    last_day: date = date.fromordinal(next_month.toordinal() - 1)
    return {"from": first_day.isoformat(), "to": last_day.isoformat()}


def pattern_sentences(
    rows: Sequence[Take5Row],
    signs: Sequence[Sign],
) -> tuple[PatternSentence, ...]:
    """Find the patterns worth a sentence, strongest first, at most `MOST_SENTENCES`.

    The strongest is the most times as common; on a tie, the sign seen most often in
    its group, then months before weekdays before times of day, each group in time
    order, and the signs in `signs`' order (S4).

    Args:
        rows: The rows.
        signs: The signs to count.

    Returns:
        The sentences.
    """
    found: list[_Comparison] = [
        comparison
        for grouping in GROUPINGS
        for group in groups_in_order(grouping, rows)
        for sign in signs
        if is_worth_a_sentence(comparison := compare(rows, grouping, group, sign))
    ]
    strongest_first: list[_Comparison] = sorted(found, key=_strongest_first)
    return tuple(
        PatternSentence(
            text=sentence_text(comparison),
            table_filters=table_filters(comparison.grouping, comparison.group),
        )
        for comparison in strongest_first[:MOST_SENTENCES]
    )


def group_counts(
    rows: Sequence[Take5Row],
    grouping: Grouping,
) -> tuple[GroupCounts, ...]:
    """Count the main signs in each group of one grouping (S5).

    Args:
        rows: The rows.
        grouping: How the Take 5s are grouped.

    Returns:
        Each group's counts, in time order.
    """
    counts: list[GroupCounts] = []
    for group in groups_in_order(grouping, rows):
        in_group: list[Take5Row] = [
            row for row in rows if grouping.group_of(row) == group
        ]
        counts.append(
            GroupCounts(
                group=month_name(group) if grouping is BY_MONTH else group,
                take5_count=len(in_group),
                high_risk_count=sum(1 for row in in_group if HIGH_RISK.shown(row)),
                rushed_count=sum(1 for row in in_group if RUSHED.shown(row)),
                thought_gaps_count=sum(
                    1 for row in in_group if THOUGHT_GAPS.shown(row)
                ),
                stopped_count=sum(1 for row in in_group if STOPPED.shown(row)),
            ),
        )
    return tuple(counts)


def patterns_over_time(
    rows: Sequence[Take5Row],
    questions: Sequence[Question],
) -> Patterns:
    """Find the patterns over time in some Take 5s, with the counts (S1 to S5).

    Args:
        rows: Every saved Take 5, laid out as a table row (E1 to E3).
        questions: The card's questions, for the hazard questions' signs.

    Returns:
        The sentences and the counts.
    """
    return Patterns(
        take5_count=len(rows),
        sentences=pattern_sentences(rows, signs_for(questions)),
        by_month=group_counts(rows, BY_MONTH),
        by_weekday=group_counts(rows, BY_WEEKDAY),
        by_time_of_day=group_counts(rows, BY_TIME_OF_DAY),
        no_time_of_day_count=sum(1 for row in rows if row.time_of_day is None),
    )
