"""The submitted verdict and template survive retries and later template changes."""

from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from uuid import UUID, uuid4

from risk_assessment.domain.controls import ControlKind
from risk_assessment.domain.take5.draft import (
    ControlDraft,
    HazardDraft,
    RatingChoice,
    Take5Draft,
)
from risk_assessment.domain.take5.saved import SavedTake5
from risk_assessment.domain.take5.template import BOOKLET_MATRIX, Take5Template
from risk_assessment.services.take5s import Take5Service
from risk_assessment.storage.sqlite import SqliteTake5Repository


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


def _draft() -> Take5Draft:
    """One controlled hazard, before and after both 8 Moderate."""
    choice = RatingChoice(likelihood="Possible", consequence="Minor")
    return Take5Draft(
        worker_name="Sam Example",
        job="Example maintenance task",
        location="Example bay",
        hazards=(
            HazardDraft(
                description="Example hazard",
                before=choice,
                after=choice,
                controls=(
                    ControlDraft(
                        description="Barricade the area", kind=ControlKind.BARRICADE
                    ),
                ),
            ),
        ),
    )


def test_the_saved_template_and_verdict_survive_a_new_template() -> None:
    """Reading or retrying must retain the original template and verdict."""
    repository = MemoryRepository()
    original_template = Take5Template(
        name="Example original card",
        matrix=BOOKLET_MATRIX.model_copy(update={"jha_threshold": 8}),
    )
    original = Take5Service(repository, original_template)
    submission_id: UUID = uuid4()
    saved: SavedTake5 = original.submit(_draft(), submission_id)
    assert not saved.verdict.can_start
    later_template = Take5Template(
        name="Example later card",
        matrix=BOOKLET_MATRIX.model_copy(update={"jha_threshold": 25}),
    )
    later = Take5Service(repository, later_template)
    assert later.get(submission_id) == saved
    assert later.submit(_draft(), submission_id) == saved
    assert len(repository.documents) == 1


def test_concurrent_retries_store_the_first_document_once(tmp_path: Path) -> None:
    """Two requests racing with the same ID return the identical stored assessment."""
    template = Take5Template(name="Example card", matrix=BOOKLET_MATRIX)
    service = Take5Service(SqliteTake5Repository(tmp_path / "take5.sqlite3"), template)
    submission_id: UUID = uuid4()

    def submit() -> SavedTake5:
        """Send the same worker input using the same submission identifier."""
        return service.submit(_draft(), submission_id)

    with ThreadPoolExecutor(max_workers=2) as pool:
        first: Future[SavedTake5] = pool.submit(submit)
        second: Future[SavedTake5] = pool.submit(submit)
        assert first.result() == second.result()
