"""Check, submit and retrieve Take 5s through a replaceable repository."""

from datetime import UTC, datetime
from uuid import UUID

from risk_assessment.domain.take5.draft import DraftCheck, Take5Draft, check_draft
from risk_assessment.domain.take5.saved import SavedTake5
from risk_assessment.domain.take5.template import Take5Template
from risk_assessment.domain.take5.verdict import verdict
from risk_assessment.services.ports import Take5Repository


class InvalidDraftError(ValueError):
    """Carry field errors back to a caller without exposing internal details."""

    def __init__(self, check: DraftCheck) -> None:
        """Keep the failed check so the API can return each field's message."""
        super().__init__("Complete the highlighted fields before submitting.")
        self.check: DraftCheck = check


class SubmissionConflictError(ValueError):
    """The same submission ID was used for different worker input."""


class Take5Service:
    """Apply the rules once, then keep the exact result the worker was given."""

    def __init__(self, repository: Take5Repository, template: Take5Template) -> None:
        """Receive storage and the current template from the composition root."""
        self._repository: Take5Repository = repository
        self._template: Take5Template = template

    def check(self, draft: Take5Draft) -> DraftCheck:
        """Check unsaved input against the current template."""
        return check_draft(draft, self._template)

    def submit(self, draft: Take5Draft, submission_id: UUID) -> SavedTake5:
        """Validate and save once; safely return the first result on a retry."""
        previous: SavedTake5 | None = self._repository.get(submission_id)
        template: Take5Template = previous.template if previous else self._template
        check: DraftCheck = check_draft(draft, template)
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
        )
        saved: SavedTake5 = previous or self._repository.add(submitted)
        if (
            saved.worker_name,
            saved.job,
            saved.location,
            saved.hazards,
            saved.template,
        ) != (
            submitted.worker_name,
            submitted.job,
            submitted.location,
            submitted.hazards,
            submitted.template,
        ):
            raise SubmissionConflictError(
                "This submission ID already belongs to another Take 5."
            )
        return saved

    def get(self, take5_id: UUID) -> SavedTake5 | None:
        """Read the saved verdict without applying today's rules again."""
        return self._repository.get(take5_id)
