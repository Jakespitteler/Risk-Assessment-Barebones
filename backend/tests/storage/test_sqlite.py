"""Tests for keeping Take 5s in SQLite."""

import json
import sqlite3
from contextlib import closing
from datetime import timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

from risk_assessment.domain.take5.saved import SavedTake5
from risk_assessment.storage.sqlite import SqliteTake5Repository
from tests.samples import sample_saved_take5


def test_a_saved_take5_reads_back_exactly_as_it_was_saved(tmp_path: Path) -> None:
    """Every field, the template copy and the verdict survive a new connection."""
    database: Path = tmp_path / "take5.sqlite3"
    take5: SavedTake5 = sample_saved_take5()

    SqliteTake5Repository(database).add(take5)

    assert SqliteTake5Repository(database).get(take5.id) == take5


def test_a_second_save_with_the_same_id_keeps_the_first(tmp_path: Path) -> None:
    """A saved Take 5 is never replaced."""
    repository = SqliteTake5Repository(tmp_path / "take5.sqlite3")
    first: SavedTake5 = sample_saved_take5()
    second: SavedTake5 = sample_saved_take5(job="Another example job").model_copy(
        update={"id": first.id},
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

    repository.add(sample_saved_take5())

    assert database.exists()


def test_the_columns_beside_the_document_are_filled_in(tmp_path: Path) -> None:
    """The table matches docs/architecture.md, so a later list can sort and find."""
    database: Path = tmp_path / "take5.sqlite3"
    take5: SavedTake5 = sample_saved_take5()

    SqliteTake5Repository(database).add(take5)

    with closing(sqlite3.connect(database)) as connection:
        row: tuple[str, str, str, str] = connection.execute(
            "SELECT id, created_at, worker_name, job FROM take5s",
        ).fetchone()
    assert row == (
        str(take5.id),
        "2026-11-13T07:30:00+00:00",
        "Sam Example",
        "Change tyre on LV12",
    )


def test_the_newest_fix_of_a_take5_is_found(tmp_path: Path) -> None:
    """`fixed_by` reads `fixes` from inside each document and picks the newest."""
    repository = SqliteTake5Repository(tmp_path / "take5.sqlite3")
    first: SavedTake5 = sample_saved_take5()
    earlier_fix: SavedTake5 = sample_saved_take5().model_copy(
        update={"fixes": first.id, "created_at": first.created_at + timedelta(hours=1)},
    )
    later_fix: SavedTake5 = sample_saved_take5().model_copy(
        update={"fixes": first.id, "created_at": first.created_at + timedelta(hours=2)},
    )
    for take5 in (first, later_fix, earlier_fix):
        repository.add(take5)

    assert repository.fixed_by(first.id) == later_fix.id
    assert repository.fixed_by(later_fix.id) is None
    assert repository.get(first.id) == first


def test_a_take5_saved_before_the_card_had_questions_still_opens(
    tmp_path: Path,
) -> None:
    """A document with no answers, on a template with no questions, reads back."""
    database: Path = tmp_path / "take5.sqlite3"
    take5: SavedTake5 = sample_saved_take5()
    old_document: dict[str, Any] = take5.model_dump(mode="json")
    del old_document["answers"]
    del old_document["template"]["questions"]
    for hazard in old_document["hazards"]:
        del hazard["weak_controls_reason"]
    with closing(sqlite3.connect(database)) as connection, connection:
        connection.execute(
            "CREATE TABLE take5s (id TEXT PRIMARY KEY, created_at TEXT, "
            "worker_name TEXT, job TEXT, document TEXT NOT NULL)",
        )
        connection.execute(
            "INSERT INTO take5s VALUES (?, ?, ?, ?, ?)",
            (str(take5.id), "", "", "", json.dumps(old_document)),
        )

    reopened: SavedTake5 | None = SqliteTake5Repository(database).get(take5.id)

    assert reopened is not None
    assert reopened.answers == {}
    assert reopened.template.questions == ()
    assert reopened.hazards[0].weak_controls_reason == ""
    assert reopened.verdict == take5.verdict
