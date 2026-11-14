"""Check, submit and get Take 5s, through storage that can be swapped."""

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


class Take5Service:
    """Apply the rules once, then keep the exact result the worker was shown."""

    def __init__(self, repository: Take5Repository, template: Take5Template) -> None:
        """Take the storage and the current template from the composition root.

        Args:
            repository: Where Take 5s are kept.
            template: The template new Take 5s are filled in on.
        """
        self._repository: Take5Repository = repository
        self._template: Take5Template = template

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
            missing.
        """
        return check_draft(draft, self._template)

    def submit(self, draft: Take5Draft, submission_id: UUID) -> SavedTake5:
        """Check and save a Take 5 once. A retry gets back what was first saved.

        Args:
            draft: The worker's answers.
            submission_id: The ID the phone made for this Take 5. It is the same on
                every retry.

        Returns:
            The saved Take 5, with its verdict.

        Raises:
            InvalidDraftError: If anything is missing, or `draft.fixes` isn't a saved
                Don't start yet.
            SubmissionConflictError: If the ID was already used for other answers.
        """
        previous: SavedTake5 | None = self._repository.get(submission_id)
        template: Take5Template = (
            previous.template if previous is not None else self._template
        )
        check: DraftCheck = self._with_fixes_error(
            check_draft(draft, template), draft.fixes, submission_id
        )
        if check.assessment is None:
            raise InvalidDraftError(check)
        now: datetime = datetime.now(UTC)
        submitted = SavedTake5(
            template=template,
            hazards=check.assessment.hazards,
            id=submission_id,
            created_at=now,
            finished_at=now,
            worker_name=draft.worker_name.strip(),
            job=draft.job.strip(),
            location=draft.location.strip(),
            verdict=verdict(check.assessment),
            fixes=draft.fixes,
        )
        saved: SavedTake5 = (
            previous if previous is not None else self._repository.add(submitted)
        )
        if _answers(saved) != _answers(submitted):
            raise SubmissionConflictError(
                "This Take 5 was already saved with different answers."
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

    def fixed_by(self, take5_id: UUID) -> UUID | None:
        """Find the newest saved Take 5 that fixes this one.

        Args:
            take5_id: The ID of the Take 5 that may have been fixed.

        Returns:
            The fix's ID, or None if it hasn't been fixed.
        """
        return self._repository.fixed_by(take5_id)

    def _with_fixes_error(
        self, check: DraftCheck, fixes: UUID | None, submission_id: UUID
    ) -> DraftCheck:
        """Add an error if the draft says it fixes a Take 5 it can't fix.

        Args:
            check: The draft's check so far.
            fixes: The ID of the Take 5 the draft says it fixes, or None.
            submission_id: The draft's own ID. A Take 5 can't fix itself.

        Returns:
            The check, with the error added and nothing to submit if there is one.
        """
        if fixes is None:
            return check
        fixed: SavedTake5 | None = (
            None if fixes == submission_id else self._repository.get(fixes)
        )
        error: FieldError | None = fixes_error(fixed)
        if error is None:
            return check
        return check.model_copy(
            update={
                "errors": (*check.errors, error),
                "assessment": None,
                "can_submit": False,
            }
        )


def _answers(take5: SavedTake5) -> dict[str, Any]:
    """Return what the worker gave and what it was filled in on, without save details.

    Args:
        take5: A saved Take 5.

    Returns:
        Its fields, without the ID, the times and the verdict.
    """
    return take5.model_dump(exclude=_SAVE_DETAILS)
