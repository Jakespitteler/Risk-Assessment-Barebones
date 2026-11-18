"""Check, submit, get and list Take 5s, through storage that can be swapped."""

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from risk_assessment.domain.take5.draft import (
    DraftCheck,
    FieldError,
    Take5Draft,
    check_draft,
)
from risk_assessment.domain.take5.fix import fixes_error
from risk_assessment.domain.take5.saved import SavedTake5
from risk_assessment.domain.take5.template import Take5Template
from risk_assessment.domain.take5.time_limit import runs_out_at, time_limit_error
from risk_assessment.domain.take5.verdict import verdict
from risk_assessment.services.ports import Take5Repository

# The fields that differ between two saves of the same answers.
_SAVE_DETAILS: set[str] = {"id", "created_at", "finished_at", "verdict"}


class InvalidDraftError(ValueError):
    """A draft that can't be submitted yet, with what is missing.

    Attributes:
        check: The failed check, with each field's error.
    """

    def __init__(self, check: DraftCheck) -> None:
        """Keep the failed check so the API can send each field's error.

        Args:
            check: The failed check.
        """
        super().__init__("Fill in the highlighted fields before you submit.")
        self.check: DraftCheck = check


class SubmissionConflictError(ValueError):
    """The submission ID was already used to save different answers."""


def utc_now() -> datetime:
    """Return the time now, in UTC: the clock the service uses unless a test swaps it.

    Returns:
        The time now.
    """
    return datetime.now(UTC)


class Take5Service:
    """Apply the rules once, then keep the exact result the worker was shown."""

    def __init__(
        self,
        repository: Take5Repository,
        template: Take5Template,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        """Take the storage, the current template and a clock from the composition root.

        Args:
            repository: Where Take 5s are kept.
            template: The template new Take 5s are filled in on.
            clock: Says what time it is now. Tests pass a fixed one.
        """
        self._repository: Take5Repository = repository
        self._template: Take5Template = template
        self._clock: Callable[[], datetime] = clock

    @property
    def template(self) -> Take5Template:
        """The template a new Take 5 is filled in on."""
        return self._template

    def check(self, draft: Take5Draft) -> DraftCheck:
        """Check a draft against the current template, without saving it.

        Args:
            draft: The worker's answers so far.

        Returns:
            What is missing, the warnings, and the rated Take 5 when nothing is
            missing, and when the draft runs out. A draft older than the template's
            time limit has an error on `started_at` (spec K2).
        """
        time_limit_minutes: int | None = self._template.draft_time_limit_minutes
        check: DraftCheck = _with_error(
            check_draft(draft, self._template),
            time_limit_error(draft.started_at, self._clock(), time_limit_minutes),
        )
        return check.model_copy(
            update={"runs_out_at": runs_out_at(draft.started_at, time_limit_minutes)},
        )

    def submit(self, draft: Take5Draft, submission_id: UUID) -> SavedTake5:
        """Check and save a Take 5 once. A retry gets back what was first saved.

        Args:
            draft: The worker's answers.
            submission_id: The ID the phone made for this Take 5. It is the same on
                every retry.

        Returns:
            The saved Take 5, with its verdict.

        Raises:
            InvalidDraftError: If anything is missing, `draft.fixes` isn't a saved
                Don't start yet, or the draft has run out (spec K2). A retry of a
                Take 5 that was saved in time is never refused for running out.
            SubmissionConflictError: If the ID was already used for other answers.
        """
        previous: SavedTake5 | None = self._repository.get(submission_id)
        template: Take5Template = (
            previous.template if previous is not None else self._template
        )
        now: datetime = self._clock()
        check: DraftCheck = _with_error(
            check_draft(draft, template),
            self._fixes_error(draft.fixes, submission_id),
        )
        if previous is None:
            check = _with_error(
                check,
                time_limit_error(
                    draft.started_at,
                    now,
                    template.draft_time_limit_minutes,
                ),
            )
        if check.assessment is None:
            raise InvalidDraftError(check)
        submitted = SavedTake5(
            template=template,
            answers=check.assessment.answers,
            hazards=check.assessment.hazards,
            id=submission_id,
            created_at=now,
            finished_at=now,
            worker_name=draft.worker_name.strip(),
            job=draft.job.strip(),
            location=draft.location.strip(),
            verdict=verdict(check.assessment),
            fixes=draft.fixes,
            started_at=draft.started_at,
        )
        saved: SavedTake5 = (
            previous if previous is not None else self._repository.add(submitted)
        )
        if _answers(saved) != _answers(submitted):
            raise SubmissionConflictError(
                "This Take 5 was already saved with different answers.",
            )
        return saved

    def get(self, take5_id: UUID) -> SavedTake5 | None:
        """Get a saved Take 5 as it was saved, without applying today's rules.

        Args:
            take5_id: The Take 5's ID.

        Returns:
            The saved Take 5, or None if there is none with this ID.
        """
        return self._repository.get(take5_id)

    def list_newest_first(self) -> tuple[SavedTake5, ...]:
        """Get every saved Take 5 as it was saved, the newest first.

        Everyone using the app sees the same list (spec decision D8).

        Returns:
            The saved Take 5s, newest first.
        """
        return self._repository.list_newest_first()

    def fixed_by(self, take5_id: UUID) -> UUID | None:
        """Find the newest saved Take 5 that fixes this one.

        Args:
            take5_id: The ID of the Take 5 that may have been fixed.

        Returns:
            The fix's ID, or None if it hasn't been fixed.
        """
        return self._repository.fixed_by(take5_id)

    def _fixes_error(
        self,
        fixes: UUID | None,
        submission_id: UUID,
    ) -> FieldError | None:
        """Say why the draft can't fix the Take 5 it says it fixes, if it can't.

        Args:
            fixes: The ID of the Take 5 the draft says it fixes, or None.
            submission_id: The draft's own ID. A Take 5 can't fix itself.

        Returns:
            The error, or None when the draft fixes nothing or may fix that Take 5.
        """
        if fixes is None:
            return None
        fixed: SavedTake5 | None = (
            None if fixes == submission_id else self._repository.get(fixes)
        )
        return fixes_error(fixed)


def _with_error(check: DraftCheck, error: FieldError | None) -> DraftCheck:
    """Add one more error to a check, which then has nothing to submit.

    Args:
        check: The draft's check so far.
        error: The error to add, or None to leave the check as it is.

    Returns:
        The check, with the error added if there is one.
    """
    if error is None:
        return check
    return check.model_copy(
        update={
            "errors": (*check.errors, error),
            "assessment": None,
            "can_submit": False,
        },
    )


def _answers(take5: SavedTake5) -> dict[str, Any]:
    """Return what the worker gave and what it was filled in on, without save details.

    Args:
        take5: A saved Take 5.

    Returns:
        Its fields, without the ID, the times and the verdict.
    """
    return take5.model_dump(exclude=_SAVE_DETAILS)
