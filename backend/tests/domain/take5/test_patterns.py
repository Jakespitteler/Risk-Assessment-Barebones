"""Tests for patterns over time in saved Take 5s (spec S1 to S5), from examples."""

from datetime import datetime, timedelta

import pytest

from risk_assessment.domain.questions import Answer
from risk_assessment.domain.take5.patterns import (
    BY_MONTH,
    BY_WEEKDAY,
    MAIN_SIGNS,
    Patterns,
    group_counts,
    patterns_over_time,
    table_filters,
)
from risk_assessment.domain.take5.table import (
    DONT_START_YET,
    GOOD_TO_GO,
    NOT_FINISHED,
    Take5Row,
)
from risk_assessment.domain.take5.template import BOOKLET_TEMPLATE
from tests.domain.take5.test_table import SATURDAY_MORNING, row, started

# Monday 23 Nov 2026, 7 am in Perth: two days after the Saturday.
MONDAY_MORNING: datetime = SATURDAY_MORNING + timedelta(days=2)
# Saturday 24 Oct 2026, 7 am in Perth: the same weekday, the month before.
OCTOBER_MORNING: datetime = SATURDAY_MORNING - timedelta(days=28)


def careful_rows(when: datetime, count: int, **changes: object) -> list[Take5Row]:
    """Make several of the careful one's rows, started at one moment.

    Args:
        when: When each was started, with its zone.
        count: How many.
        **changes: Values to change on each row, such as `rushed=True`.

    Returns:
        The rows.
    """
    careful: Take5Row = row(started(when)).model_copy(update=changes)
    return [careful] * count


def found(rows: list[Take5Row]) -> Patterns:
    """Find the patterns in rows, on the booklet's questions.

    Args:
        rows: The rows.

    Returns:
        The patterns.
    """
    return patterns_over_time(rows, BOOKLET_TEMPLATE.questions)


def sentences(rows: list[Take5Row]) -> list[str]:
    """Find just the sentences' words.

    Args:
        rows: The rows.

    Returns:
        Each sentence's text, strongest first.
    """
    return [sentence.text for sentence in found(rows).sentences]


def test_example_156_rushed_take5s_stand_out_on_saturdays() -> None:
    """S3, S4: 5 of 10 rushed on Saturdays against 1 of 10 on Mondays is 5 times."""
    rows: list[Take5Row] = [
        *careful_rows(SATURDAY_MORNING, 5, rushed=True),
        *careful_rows(SATURDAY_MORNING, 5),
        *careful_rows(MONDAY_MORNING, 1, rushed=True),
        *careful_rows(MONDAY_MORNING, 9),
    ]

    assert sentences(rows) == [
        "5 of 10 timed Take 5s on Saturdays were rushed: 5 times the rate on other "
        "days (1 of 10).",
    ]


def test_example_157_a_sign_never_seen_elsewhere() -> None:
    """S4: 3 of 5 high risk on Mondays, none of 5 elsewhere: the smallest sizes."""
    rows: list[Take5Row] = [
        *careful_rows(MONDAY_MORNING, 3, needs_jha=True),
        *careful_rows(MONDAY_MORNING, 2),
        *careful_rows(SATURDAY_MORNING, 5),
    ]

    assert sentences(rows) == [
        "3 of 5 Take 5s on Mondays were high risk, and none of 5 on other days.",
    ]


@pytest.mark.parametrize(
    ("rows"),
    [
        pytest.param(
            [
                *careful_rows(MONDAY_MORNING, 4, needs_jha=True),
                *careful_rows(SATURDAY_MORNING, 10),
            ],
            id="example_158_a_group_of_four",
        ),
        pytest.param(
            [
                *careful_rows(MONDAY_MORNING, 5, needs_jha=True),
                *careful_rows(SATURDAY_MORNING, 4),
            ],
            id="example_158_four_elsewhere",
        ),
        pytest.param(
            [
                *careful_rows(MONDAY_MORNING, 2, needs_jha=True),
                *careful_rows(MONDAY_MORNING, 3),
                *careful_rows(SATURDAY_MORNING, 10),
            ],
            id="example_159_seen_twice",
        ),
    ],
)
def test_examples_158_and_159_too_few_is_no_sentence(rows: list[Take5Row]) -> None:
    """S4: fewer than 5 on either side, or a sign seen under 3 times, says nothing."""
    assert sentences(rows) == []


def test_example_160_exactly_twice_is_a_sentence() -> None:
    """S4: 4 of 10 against 2 of 10 is exactly twice; against 3 of 10 it isn't."""
    twice: list[Take5Row] = [
        *careful_rows(MONDAY_MORNING, 4, rushed=True),
        *careful_rows(MONDAY_MORNING, 6),
        *careful_rows(SATURDAY_MORNING, 2, rushed=True),
        *careful_rows(SATURDAY_MORNING, 8),
    ]
    under_twice: list[Take5Row] = [
        *careful_rows(MONDAY_MORNING, 4, rushed=True),
        *careful_rows(MONDAY_MORNING, 6),
        *careful_rows(SATURDAY_MORNING, 3, rushed=True),
        *careful_rows(SATURDAY_MORNING, 7),
    ]

    assert sentences(twice) == [
        "4 of 10 timed Take 5s on Mondays were rushed: twice the rate on other days "
        "(2 of 10).",
    ]
    assert sentences(under_twice) == []


def test_example_161_only_finished_take5s_have_a_verdict() -> None:
    """S3: unfinished Take 5s are on neither side of "Don't start yet"."""
    rows: list[Take5Row] = [
        *careful_rows(MONDAY_MORNING, 3, verdict=DONT_START_YET),
        *careful_rows(MONDAY_MORNING, 2, verdict=GOOD_TO_GO),
        *careful_rows(MONDAY_MORNING, 2, verdict=NOT_FINISHED),
        *careful_rows(SATURDAY_MORNING, 5, verdict=GOOD_TO_GO),
    ]

    assert sentences(rows) == [
        "3 of 5 finished Take 5s on Mondays were told “Don’t start yet”, and none of "
        "5 on other days.",
    ]


def test_a_take5_with_no_time_taken_is_never_counted_as_rushed() -> None:
    """S3: paper cards and Take 5s with no start time are on neither side of rushed."""
    rows: list[Take5Row] = [
        *careful_rows(MONDAY_MORNING, 3, rushed=True),
        *careful_rows(MONDAY_MORNING, 4, minutes_taken=None),
        *careful_rows(MONDAY_MORNING, 2),
        *careful_rows(SATURDAY_MORNING, 5),
    ]

    assert sentences(rows) == [
        "3 of 5 timed Take 5s on Mondays were rushed, and none of 5 on other days.",
    ]


def test_example_162_a_hazard_question_answered_yes_in_one_month() -> None:
    """S3, S4: Yes to "other" hazards in November, linked to that month in the table."""
    no_to_other: dict[str, str] = {"other": Answer.NO}
    yes_to_other: dict[str, str] = {"other": Answer.YES}
    rows: list[Take5Row] = [
        *careful_rows(SATURDAY_MORNING, 3, answers=yes_to_other),
        *careful_rows(SATURDAY_MORNING, 2, answers=no_to_other),
        *careful_rows(OCTOBER_MORNING, 5, answers=no_to_other),
    ]

    patterns: Patterns = found(rows)

    assert [sentence.text for sentence in patterns.sentences] == [
        "3 of 5 Take 5s in November 2026 answered Yes to “Other environmental and/or "
        "H&S hazards?”, and none of 5 in other months.",
    ]
    assert patterns.sentences[0].table_filters == {
        "from": "2026-11-01",
        "to": "2026-11-30",
    }


def test_example_163_a_paper_card_with_no_time_is_left_out_by_time_of_day() -> None:
    """S2: 3 of 5 rushed in the morning; 6 with no time aren't compared."""
    rows: list[Take5Row] = [
        *careful_rows(MONDAY_MORNING, 3, rushed=True),
        *careful_rows(MONDAY_MORNING, 2),
        *careful_rows(MONDAY_MORNING + timedelta(hours=8), 5),
        *careful_rows(
            MONDAY_MORNING,
            6,
            time_of_day=None,
            minutes_taken=None,
            needs_jha=True,
        ),
    ]

    patterns: Patterns = found(rows)

    assert [sentence.text for sentence in patterns.sentences] == [
        "3 of 5 timed Take 5s from 6 am to noon were rushed, and none of 5 at other "
        "times of day.",
    ]
    assert patterns.no_time_of_day_count == 6
    assert [counts.take5_count for counts in patterns.by_time_of_day] == [0, 5, 5, 0]


def test_example_164_at_most_five_sentences_strongest_first() -> None:
    """S4: nine found; five shown, never seen elsewhere first, then card order."""
    yes_to_every_hazard: dict[str, str] = {
        question.id: Answer.YES for question in BOOKLET_TEMPLATE.questions
    }
    rows: list[Take5Row] = [
        *careful_rows(
            MONDAY_MORNING,
            5,
            needs_jha=True,
            answers=yes_to_every_hazard,
        ),
        *careful_rows(MONDAY_MORNING, 5, rushed=True),
        *careful_rows(SATURDAY_MORNING, 9),
        *careful_rows(SATURDAY_MORNING, 1, rushed=True),
    ]

    texts: list[str] = sentences(rows)

    assert len(texts) == 5
    assert texts[0] == (
        "5 of 10 Take 5s on Mondays were high risk, and none of 10 on other days."
    )
    assert texts[-1] == (
        "5 of 10 Take 5s on Mondays answered Yes to “Will I be performing a task "
        "without a specific isolation procedure?”, and none of 10 on other days."
    )
    assert "were rushed" not in " ".join(texts)


def test_example_165_counts_by_weekday_and_month() -> None:
    """S5: every weekday from Monday, zeros too; only months with a Take 5, in words."""
    rows: list[Take5Row] = [
        *careful_rows(MONDAY_MORNING, 2, needs_jha=True, rushed=True),
        *careful_rows(SATURDAY_MORNING, 1, verdict=DONT_START_YET),
        *careful_rows(OCTOBER_MORNING, 1, thought_gaps=("a gap",)),
    ]

    by_weekday = group_counts(rows, BY_WEEKDAY)
    by_month = group_counts(rows, BY_MONTH)

    assert [counts.group for counts in by_weekday] == [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    monday = by_weekday[0]
    assert (
        monday.take5_count,
        monday.high_risk_count,
        monday.rushed_count,
        monday.thought_gaps_count,
        monday.stopped_count,
    ) == (2, 2, 2, 0, 0)
    assert by_weekday[5].stopped_count == 1
    assert by_weekday[1].take5_count == 0
    assert [(counts.group, counts.take5_count) for counts in by_month] == [
        ("October 2026", 1),
        ("November 2026", 3),
    ]
    assert by_month[0].thought_gaps_count == 1


def test_nothing_saved_finds_nothing() -> None:
    """S1: with no Take 5s there are no sentences, and every count is zero."""
    patterns: Patterns = found([])

    assert patterns.take5_count == 0
    assert patterns.sentences == ()
    assert patterns.by_month == ()
    assert all(counts.take5_count == 0 for counts in patterns.by_weekday)


def test_a_december_month_links_to_its_last_day() -> None:
    """S4: the table link for December runs to 31 December, not into the next year."""
    assert table_filters(BY_MONTH, "2026-12") == {
        "from": "2026-12-01",
        "to": "2026-12-31",
    }


def test_a_weekday_links_by_its_name() -> None:
    """S4: a weekday or time of day links to the table's own filter for it."""
    assert table_filters(BY_WEEKDAY, "Monday") == {"weekday": "Monday"}


def test_the_main_signs_come_before_the_hazard_questions() -> None:
    """S3: four main signs, in the order a tie between sentences goes by."""
    assert [sign.described for sign in MAIN_SIGNS] == [
        "were high risk",
        "were rushed",
        "had thought gaps",
        "were told “Don’t start yet”",
    ]


def test_ten_times_or_more_is_a_whole_number() -> None:
    """S4: 6 of 9 against 1 of 43 is 28.7 times, said as 29."""
    rows: list[Take5Row] = [
        *careful_rows(MONDAY_MORNING, 6, rushed=True),
        *careful_rows(MONDAY_MORNING, 3),
        *careful_rows(SATURDAY_MORNING, 1, rushed=True),
        *careful_rows(SATURDAY_MORNING, 42),
    ]

    assert sentences(rows) == [
        "6 of 9 timed Take 5s on Mondays were rushed: 29 times the rate on other days "
        "(1 of 43).",
    ]
