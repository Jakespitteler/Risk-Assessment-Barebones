"""How long a Take 5 can be left unfinished before it runs out (spec K2).

A Take 5 is meant to be done at the job, just before starting. A draft left for hours
could be started at breakfast and finished at lunch without looking again, so a draft
older than its template's time limit can't be submitted. A template with no time limit
turns the check off completely.

The phone says when the worker started the draft; the caller says what time it is now,
so this rule never reads a clock.
"""

from datetime import datetime, timedelta

from risk_assessment.domain.take5.draft import FieldError

STARTED_AT_PATH: str = "started_at"
MINUTES_IN_AN_HOUR: int = 60


def time_limit_error(
    started_at: datetime | None,
    now: datetime,
    time_limit_minutes: int | None,
) -> FieldError | None:
    """Say that a draft has run out, if it is older than the time limit.

    A draft exactly on the limit can still be used. A start time in the future, from
    a phone whose clock was changed, is treated as just started.

    Args:
        started_at: When the worker started the draft, or None if the phone didn't
            say. A draft with no start time isn't checked.
        now: The time to check it at.
        time_limit_minutes: How many minutes a draft lasts, or None for no limit.

    Returns:
        The error to show, or None while the draft can still be used.
    """
    deadline: datetime | None = runs_out_at(started_at, time_limit_minutes)
    if deadline is None or time_limit_minutes is None or now <= deadline:
        return None
    return FieldError(path=STARTED_AT_PATH, message=run_out_message(time_limit_minutes))


def runs_out_at(
    started_at: datetime | None,
    time_limit_minutes: int | None,
) -> datetime | None:
    """Work out when a draft runs out, so the phone can show the time it has left.

    Args:
        started_at: When the worker started the draft, or None if the phone didn't
            say.
        time_limit_minutes: How many minutes a draft lasts, or None for no limit.

    Returns:
        The last moment the draft can still be used, or None when it never runs out.
    """
    if started_at is None or time_limit_minutes is None:
        return None
    return started_at + timedelta(minutes=time_limit_minutes)


def run_out_message(time_limit_minutes: int) -> str:
    """Tell the worker their draft ran out, in plain words.

    Args:
        time_limit_minutes: How many minutes a draft lasts.

    Returns:
        The message, such as "This Take 5 was started more than 2 hours ago. Start a
        new one at the job."
    """
    return (
        f"This Take 5 was started more than {_duration(time_limit_minutes)} ago. "
        "Start a new one at the job."
    )


def _duration(minutes: int) -> str:
    """Write a number of minutes as hours when it is whole hours, such as "2 hours".

    Args:
        minutes: How many minutes.

    Returns:
        The duration in words.
    """
    hours, leftover_minutes = divmod(minutes, MINUTES_IN_AN_HOUR)
    if leftover_minutes:
        return f"{minutes} minute{'' if minutes == 1 else 's'}"
    return f"{hours} hour{'' if hours == 1 else 's'}"
