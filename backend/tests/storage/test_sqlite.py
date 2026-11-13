"""Tests for keeping Take 5s in SQLite."""

import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from risk_assessment.domain.controls import Control, ControlKind
from risk_assessment.domain.risk import rate
from risk_assessment.domain.take5.saved import SavedTake5
from risk_assessment.domain.take5.take5 import Hazard
from risk_assessment.domain.take5.template import BOOKLET_MATRIX, BOOKLET_TEMPLATE
from risk_assessment.domain.take5.verdict import Verdict
from risk_assessment.storage.sqlite import SqliteTake5Repository


def _saved(job: str = "Change tyre on LV12") -> SavedTake5:
    """A saved Take 5 with one controlled hazard and every field filled in."""
    now: datetime = datetime(2026, 11, 13, 7, 30, tzinfo=UTC)
    return SavedTake5(
        template=BOOKLET_TEMPLATE,
        hazards=(
            Hazard(
                description="Moving wheel",
                before=rate(BOOKLET_MATRIX, "Possible", "Minor"),
                controls=(
                    Control(
                        description="Barricade the area", kind=ControlKind.BARRICADE
                    ),
                ),
                after=rate(BOOKLET_MATRIX, "Unlikely", "Minor"),
            ),
        ),
        id=uuid4(),
        created_at=now,
        finished_at=now,
        worker_name="Sam Example",
        job=job,
        location="Example workshop",
        verdict=Verdict(can_start=True, reasons=()),
    )


def test_a_saved_take5_reads_back_exactly_as_it_was_saved(tmp_path: Path) -> None:
    """Every field, the template copy and the verdict survive a new connection."""
    database: Path = tmp_path / "take5.sqlite3"
    take5: SavedTake5 = _saved()

    SqliteTake5Repository(database).add(take5)

    assert SqliteTake5Repository(database).get(take5.id) == take5


def test_a_second_save_with_the_same_id_keeps_the_first(tmp_path: Path) -> None:
    """A saved Take 5 is never replaced."""
    repository = SqliteTake5Repository(tmp_path / "take5.sqlite3")
    first: SavedTake5 = _saved()
    second: SavedTake5 = _saved(job="Another example job").model_copy(
        update={"id": first.id}
    )

    repository.add(first)

    assert repository.add(second) == first
    assert repository.get(first.id) == first


def test_an_unknown_id_finds_nothing(tmp_path: Path) -> None:
    """Asking for an ID that was never saved returns None."""
    assert SqliteTake5Repository(tmp_path / "take5.sqlite3").get(uuid4()) is None


def test_the_file_and_its_folder_are_made_on_first_use(tmp_path: Path) -> None:
    """Making the repository opens nothing; the first save makes the file."""
    database: Path = tmp_path / "new folder" / "take5.sqlite3"
    repository = SqliteTake5Repository(database)
    assert not database.exists()

    repository.add(_saved())

    assert database.exists()


def test_the_columns_beside_the_document_are_filled_in(tmp_path: Path) -> None:
    """The table matches docs/architecture.md, so a later list can sort and find."""
    database: Path = tmp_path / "take5.sqlite3"
    take5: SavedTake5 = _saved()

    SqliteTake5Repository(database).add(take5)

    with closing(sqlite3.connect(database)) as connection:
        row: tuple[str, str, str, str] = connection.execute(
            "SELECT id, created_at, worker_name, job FROM take5s"
        ).fetchone()
    assert row == (
        str(take5.id),
        "2026-11-13T07:30:00+00:00",
        "Sam Example",
        "Change tyre on LV12",
    )
