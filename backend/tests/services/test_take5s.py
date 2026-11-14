"""The submitted verdict and template survive retries and later template changes."""

from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from risk_assessment.domain.take5.draft import (
    FieldError,
    Take5Draft,
)
from risk_assessment.domain.take5.fix import NOT_SAVED_MESSAGE, NOTHING_TO_FIX_MESSAGE
from risk_assessment.domain.take5.saved import SavedTake5
from risk_assessment.domain.take5.template import BOOKLET_MATRIX, Take5Template
from risk_assessment.services.take5s import InvalidDraftError, Take5Service
from risk_assessment.storage.sqlite import SqliteTake5Repository
from tests.samples import (
    sample_draft,
    sample_hazard_draft,
    sample_uncontrolled_draft,
)


class MemoryRepository:
    """A second implementation proves the service needs no SQLite-specific methods."""

    def __init__(self) -> None:
        """Start with an empty document collection."""
        self.documents: dict[UUID, SavedTake5] = {}

    def add(self, take5: SavedTake5) -> SavedTake5:
        """Keep the first document for each ID."""
        return self.documents.setdefault(take5.id, take5)

    def get(self, take5_id: UUID) -> SavedTake5 | None:
        """Read the document or return nothing."""
        return self.documents.get(take5_id)

    def fixed_by(self, take5_id: UUID) -> UUID | None:
        """Return the newest document whose `fixes` is this ID."""
        fixes: list[SavedTake5] = [
            take5 for take5 in self.documents.values() if take5.fixes == take5_id
        ]
        newest: SavedTake5 | None = max(
            fixes,
            key=lambda take5: take5.created_at,
            default=None,
        )
        return newest.id if newest is not None else None


def test_the_saved_template_and_verdict_survive_a_new_template() -> None:
    """Reading or retrying must retain the original template and verdict."""
    draft_rated_8_after: Take5Draft = sample_draft(
        sample_hazard_draft(after=("Possible", "Minor")),
    )
    repository = MemoryRepository()
    original_template = Take5Template(
        name="Example original card",
        matrix=BOOKLET_MATRIX.model_copy(update={"jha_threshold": 8}),
    )
    original = Take5Service(repository, original_template)
    submission_id: UUID = uuid4()
    saved: SavedTake5 = original.submit(draft_rated_8_after, submission_id)
    assert not saved.verdict.can_start
    later_template = Take5Template(
        name="Example later card",
        matrix=BOOKLET_MATRIX.model_copy(update={"jha_threshold": 25}),
    )
    later = Take5Service(repository, later_template)
    assert later.get(submission_id) == saved
    assert later.submit(draft_rated_8_after, submission_id) == saved
    assert len(repository.documents) == 1


def test_concurrent_retries_store_the_first_document_once(tmp_path: Path) -> None:
    """Two requests racing with the same ID return the identical stored assessment."""
    template = Take5Template(name="Example card", matrix=BOOKLET_MATRIX)
    service = Take5Service(SqliteTake5Repository(tmp_path / "take5.sqlite3"), template)
    submission_id: UUID = uuid4()

    def submit() -> SavedTake5:
        """Send the same worker input using the same submission identifier."""
        return service.submit(sample_draft(), submission_id)

    with ThreadPoolExecutor(max_workers=2) as pool:
        first: Future[SavedTake5] = pool.submit(submit)
        second: Future[SavedTake5] = pool.submit(submit)
        assert first.result() == second.result()


def _service() -> Take5Service:
    """A service on the booklet's matrix with nothing saved yet."""
    template = Take5Template(name="Example card", matrix=BOOKLET_MATRIX)
    return Take5Service(MemoryRepository(), template)


def _fixes_errors(service: Take5Service, draft: Take5Draft) -> tuple[FieldError, ...]:
    """Submit a draft that should be refused, and return the errors it got.

    Args:
        service: The service to submit to.
        draft: A draft that can't be submitted.

    Returns:
        The refusal's errors.
    """
    with pytest.raises(InvalidDraftError) as refusal:
        service.submit(draft, uuid4())
    return refusal.value.check.errors


def test_a_fix_points_back_and_the_first_take5_is_unchanged() -> None:
    """The fix records `fixes`; the first is found to be fixed but never rewritten."""
    service: Take5Service = _service()
    first: SavedTake5 = service.submit(sample_uncontrolled_draft(), uuid4())

    fix: SavedTake5 = service.submit(
        sample_draft().model_copy(update={"fixes": first.id}),
        uuid4(),
    )

    assert fix.fixes == first.id
    assert fix.verdict.can_start
    assert service.get(first.id) == first
    assert service.fixed_by(first.id) == fix.id
    assert service.fixed_by(fix.id) is None


def test_the_newest_fix_is_the_one_found() -> None:
    """If a Take 5 is fixed twice, its result links to the later fix."""
    service: Take5Service = _service()
    first: SavedTake5 = service.submit(sample_uncontrolled_draft(), uuid4())
    fixed: Take5Draft = sample_draft().model_copy(update={"fixes": first.id})

    service.submit(fixed, uuid4())
    later: SavedTake5 = service.submit(fixed, uuid4())

    assert service.fixed_by(first.id) == later.id


def test_a_fix_of_a_take5_that_is_not_saved_is_refused() -> None:
    """The phone can't link a new Take 5 to one that doesn't exist."""
    draft: Take5Draft = sample_draft().model_copy(update={"fixes": uuid4()})

    assert _fixes_errors(_service(), draft) == (
        FieldError(path="fixes", message=NOT_SAVED_MESSAGE),
    )


def test_a_fix_of_a_good_to_go_is_refused() -> None:
    """Only a Don't start yet has something to fix."""
    service: Take5Service = _service()
    good_to_go: SavedTake5 = service.submit(sample_draft(), uuid4())
    draft: Take5Draft = sample_draft().model_copy(update={"fixes": good_to_go.id})

    assert _fixes_errors(service, draft) == (
        FieldError(path="fixes", message=NOTHING_TO_FIX_MESSAGE),
    )


def test_a_take5_cannot_fix_itself() -> None:
    """A retry of a Take 5 that names its own ID is refused, not linked to itself."""
    service: Take5Service = _service()
    submission_id: UUID = uuid4()
    first: SavedTake5 = service.submit(sample_uncontrolled_draft(), submission_id)
    draft: Take5Draft = sample_uncontrolled_draft().model_copy(
        update={"fixes": submission_id},
    )

    with pytest.raises(InvalidDraftError) as refusal:
        service.submit(draft, submission_id)

    assert refusal.value.check.errors == (
        FieldError(path="fixes", message=NOT_SAVED_MESSAGE),
    )
    assert service.get(submission_id) == first
    assert service.fixed_by(submission_id) is None
