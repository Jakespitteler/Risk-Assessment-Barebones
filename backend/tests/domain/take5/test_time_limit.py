"""Spec K2: a draft older than its template's time limit has run out."""

from datetime import UTC, datetime, timedelta

import pytest

from risk_assessment.domain.take5.draft import FieldError
from risk_assessment.domain.take5.time_limit import (
    STARTED_AT_PATH,
    run_out_message,
    time_limit_error,
)

CHECKED_AT = datetime(2026, 11, 15, 20, 12, tzinfo=UTC)
BOOKLET_LIMIT_MINUTES: int = 120
RUN_OUT = FieldError(
    path=STARTED_AT_PATH,
    message=(
        "This Take 5 was started more than 2 hours ago. Start a new one at the job."
    ),
)


@pytest.mark.parametrize(
    ("started_before_check", "time_limit_minutes", "expected"),
    [
        pytest.param(
            timedelta(hours=1, minutes=59),
            BOOKLET_LIMIT_MINUTES,
            None,
            id="example_57_inside_the_limit",
        ),
        pytest.param(
            timedelta(hours=2),
            BOOKLET_LIMIT_MINUTES,
            None,
            id="example_58_exactly_on_the_limit",
        ),
        pytest.param(
            timedelta(hours=2, seconds=1),
            BOOKLET_LIMIT_MINUTES,
            RUN_OUT,
            id="example_59_one_second_over",
        ),
        pytest.param(
            timedelta(days=3),
            None,
            None,
            id="example_60_no_time_limit",
        ),
        pytest.param(
            -timedelta(minutes=5),
            BOOKLET_LIMIT_MINUTES,
            None,
            id="example_61_started_in_the_future",
        ),
    ],
)
def test_examples_57_to_61_when_a_draft_runs_out(
    started_before_check: timedelta,
    time_limit_minutes: int | None,
    expected: FieldError | None,
) -> None:
    """Only a draft more than the limit old runs out, and no limit means never."""
    started_at: datetime = CHECKED_AT - started_before_check

    assert time_limit_error(started_at, CHECKED_AT, time_limit_minutes) == expected


def test_example_62_a_draft_with_no_start_time_is_not_checked() -> None:
    """A phone from before task 0019 sends no start time, so nothing is checked."""
    assert time_limit_error(None, CHECKED_AT, BOOKLET_LIMIT_MINUTES) is None


@pytest.mark.parametrize(
    ("time_limit_minutes", "expected_duration"),
    [
        (1, "1 minute"),
        (90, "90 minutes"),
        (60, "1 hour"),
        (720, "12 hours"),
    ],
)
def test_the_message_names_the_time_limit_in_plain_words(
    time_limit_minutes: int,
    expected_duration: str,
) -> None:
    """Whole hours are written as hours, anything else as minutes."""
    assert run_out_message(time_limit_minutes) == (
        f"This Take 5 was started more than {expected_duration} ago. "
        "Start a new one at the job."
    )
