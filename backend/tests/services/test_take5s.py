"""The submitted verdict and template survive retries and later template changes."""

from concurrent.futures import Future, ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from risk_assessment.domain.take5.draft import (
    DraftCheck,
    FieldError,
    Take5Draft,
)
from risk_assessment.domain.take5.fix import NOT_SAVED_MESSAGE, NOTHING_TO_FIX_MESSAGE
from risk_assessment.domain.take5.saved import SavedTake5
from risk_assessment.domain.take5.template import (
    BOOKLET_MATRIX,
    BOOKLET_TEMPLATE,
    Take5Template,
)
from risk_assessment.domain.take5.time_limit import STARTED_AT_PATH, run_out_message
from risk_assessment.services.take5s import InvalidDraftError, Take5Service
from risk_assessment.storage.sqlite import SqliteTake5Repository
from tests.samples import (
    SAMPLE_ANSWER,
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

    def save_question(self, take5: SavedTake5) -> SavedTake5:
        """Replace an unfinished document with no question yet."""
        stored: SavedTake5 = self.documents[take5.id]
        if stored.challenge is None and not stored.is_finished:
            self.documents[take5.id] = take5
        return self.documents[take5.id]

    def finish(self, take5: SavedTake5) -> SavedTake5:
        """Replace an unfinished document."""
        if not self.documents[take5.id].is_finished:
            self.documents[take5.id] = take5
        return self.documents[take5.id]

    def get(self, take5_id: UUID) -> SavedTake5 | None:
        """Read the document or return nothing."""
        return self.documents.get(take5_id)

    def list_newest_first(self) -> tuple[SavedTake5, ...]:
        """Return every document, newest first, the last saved first on a tie."""
        last_saved_first: list[SavedTake5] = list(reversed(self.documents.values()))
        return tuple(
            sorted(
                last_saved_first,
                key=lambda take5: take5.created_at,
                reverse=True,
            ),
        )

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


def _finish(
    service: Take5Service,
    draft: Take5Draft,
    submission_id: UUID | None = None,
) -> SavedTake5:
    """Submit a draft and answer its question, so it has its verdict.

    Args:
        service: The service to submit to.
        draft: The worker's answers.
        submission_id: The submission ID, or None for a new one.

    Returns:
        The finished Take 5.
    """
    saved: SavedTake5 = service.submit(draft, submission_id or uuid4())
    return service.answer(saved.id, SAMPLE_ANSWER)


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
    saved: SavedTake5 = _finish(original, draft_rated_8_after, submission_id)
    assert saved.verdict is not None and not saved.verdict.can_start
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
    first: SavedTake5 = _finish(service, sample_uncontrolled_draft())

    fix: SavedTake5 = _finish(
        service,
        sample_draft().model_copy(update={"fixes": first.id}),
    )

    assert fix.fixes == first.id
    assert fix.verdict is not None and fix.verdict.can_start
    assert service.get(first.id) == first
    assert service.fixed_by(first.id) == fix.id
    assert service.fixed_by(fix.id) is None


def test_the_newest_fix_is_the_one_found() -> None:
    """If a Take 5 is fixed twice, its result links to the later fix."""
    service: Take5Service = _service()
    first: SavedTake5 = _finish(service, sample_uncontrolled_draft())
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
    good_to_go: SavedTake5 = _finish(service, sample_draft())
    draft: Take5Draft = sample_draft().model_copy(update={"fixes": good_to_go.id})

    assert _fixes_errors(service, draft) == (
        FieldError(path="fixes", message=NOTHING_TO_FIX_MESSAGE),
    )


def test_a_take5_cannot_fix_itself() -> None:
    """A retry of a Take 5 that names its own ID is refused, not linked to itself."""
    service: Take5Service = _service()
    submission_id: UUID = uuid4()
    first: SavedTake5 = _finish(service, sample_uncontrolled_draft(), submission_id)
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


def test_the_list_is_newest_first_with_each_verdict_as_it_was_saved() -> None:
    """Listing applies no rules: each Take 5 keeps the verdict it was saved with."""
    service: Take5Service = _service()
    stopped: SavedTake5 = _finish(service, sample_uncontrolled_draft())
    good_to_go: SavedTake5 = _finish(service, sample_draft())

    listed: tuple[SavedTake5, ...] = service.list_newest_first()

    assert listed == (good_to_go, stopped)
    assert [take5.verdict for take5 in listed] == [
        good_to_go.verdict,
        stopped.verdict,
    ]
    assert good_to_go.verdict is not None and good_to_go.verdict.can_start


def test_the_list_is_empty_before_anything_is_saved() -> None:
    """A new app has nothing to list."""
    assert _service().list_newest_first() == ()


STARTED_AT = datetime(2026, 11, 15, 20, 12, tzinfo=UTC)


def _service_at(clock_reading: list[datetime]) -> Take5Service:
    """A booklet service with nothing saved, whose clock reads the list's only item.

    Args:
        clock_reading: A one-item list. A test changes the item to move the clock on.

    Returns:
        The service.
    """
    return Take5Service(MemoryRepository(), BOOKLET_TEMPLATE, lambda: clock_reading[0])


def _started_draft() -> Take5Draft:
    """The sample draft, started at `STARTED_AT`."""
    return sample_draft().model_copy(update={"started_at": STARTED_AT})


def test_the_check_says_when_a_draft_has_run_out() -> None:
    """Checking a draft past the booklet's 2 hours gives the run-out error (K2)."""
    service: Take5Service = _service_at([STARTED_AT + timedelta(hours=2, seconds=1)])

    check: DraftCheck = service.check(_started_draft())

    assert check.errors == (
        FieldError(path=STARTED_AT_PATH, message=run_out_message(120)),
    )
    assert not check.can_submit
    assert check.assessment is None


def test_a_draft_that_has_run_out_cannot_be_submitted() -> None:
    """Submitting past the time limit is refused, and nothing is saved (K2)."""
    clock_reading: list[datetime] = [STARTED_AT + timedelta(hours=3)]
    service: Take5Service = _service_at(clock_reading)

    with pytest.raises(InvalidDraftError) as refusal:
        service.submit(_started_draft(), uuid4())

    assert [error.path for error in refusal.value.check.errors] == [STARTED_AT_PATH]
    assert service.list_newest_first() == ()


def test_example_62_a_draft_with_no_start_time_is_saved_without_one() -> None:
    """A phone that sends no start time isn't checked, however late it submits (K2)."""
    service: Take5Service = _service_at([STARTED_AT + timedelta(days=3)])

    assert service.check(sample_draft()).can_submit
    assert service.submit(sample_draft(), uuid4()).started_at is None


def test_example_63_the_start_time_is_saved_with_the_take5() -> None:
    """Submitted 4 minutes after starting, it is saved with when it was started (K3)."""
    service: Take5Service = _service_at([STARTED_AT + timedelta(minutes=4)])

    saved: SavedTake5 = service.submit(_started_draft(), uuid4())

    assert saved.started_at == STARTED_AT
    assert saved.created_at == STARTED_AT + timedelta(minutes=4)


def test_example_64_a_retry_after_the_limit_returns_what_was_saved_in_time() -> None:
    """A lost answer retried after the limit gets the Take 5 saved in time (K2)."""
    clock_reading: list[datetime] = [STARTED_AT + timedelta(minutes=4)]
    service: Take5Service = _service_at(clock_reading)
    submission_id: UUID = uuid4()
    saved: SavedTake5 = service.submit(_started_draft(), submission_id)

    clock_reading[0] = STARTED_AT + timedelta(hours=5)

    assert service.submit(_started_draft(), submission_id) == saved


def test_a_template_with_no_time_limit_never_runs_out() -> None:
    """With the limit switched off, a draft started days ago can still be submitted."""
    template: Take5Template = BOOKLET_TEMPLATE.model_copy(
        update={"draft_time_limit_minutes": None},
    )
    service = Take5Service(
        MemoryRepository(),
        template,
        lambda: STARTED_AT + timedelta(days=3),
    )

    assert service.check(_started_draft()).can_submit
    assert service.submit(_started_draft(), uuid4()).started_at == STARTED_AT


def test_the_check_says_when_the_draft_runs_out() -> None:
    """The phone shows the time left from this; the timer off sends nothing (K2)."""
    service: Take5Service = _service_at([STARTED_AT + timedelta(minutes=10)])
    no_limit = Take5Service(
        MemoryRepository(),
        BOOKLET_TEMPLATE.model_copy(update={"draft_time_limit_minutes": None}),
        lambda: STARTED_AT,
    )

    assert service.check(_started_draft()).runs_out_at == STARTED_AT + timedelta(
        hours=2,
    )
    assert no_limit.check(_started_draft()).runs_out_at is None
