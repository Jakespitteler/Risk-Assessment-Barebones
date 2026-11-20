"""Tests for keeping Take 5s in SQLite."""

import json
import sqlite3
from contextlib import closing
from datetime import timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

from risk_assessment.domain.take5.challenge import AskedBy, Challenge
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
    """A document with no answers or links, on a card with no questions, reads back."""
    database: Path = tmp_path / "take5.sqlite3"
    take5: SavedTake5 = sample_saved_take5()
    old_document: dict[str, Any] = take5.model_dump(mode="json")
    del old_document["answers"]
    del old_document["template"]["questions"]
    for hazard in old_document["hazards"]:
        del hazard["weak_controls_reason"]
        del hazard["covers"]
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
    assert reopened.hazards[0].covers == ()
    assert reopened.verdict == take5.verdict


def test_the_list_is_newest_first_whatever_order_they_were_saved_in(
    tmp_path: Path,
) -> None:
    """The list sorts by when each Take 5 was saved, not by the order of the rows."""
    repository = SqliteTake5Repository(tmp_path / "take5.sqlite3")
    oldest: SavedTake5 = sample_saved_take5(job="Oldest example job")
    newest: SavedTake5 = sample_saved_take5(job="Newest example job").model_copy(
        update={"created_at": oldest.created_at + timedelta(hours=2)},
    )
    middle: SavedTake5 = sample_saved_take5(job="Middle example job").model_copy(
        update={"created_at": oldest.created_at + timedelta(hours=1, microseconds=5)},
    )
    for take5 in (middle, oldest, newest):
        repository.add(take5)

    assert SqliteTake5Repository(tmp_path / "take5.sqlite3").list_newest_first() == (
        newest,
        middle,
        oldest,
    )


def test_a_whole_second_lists_before_a_fraction_of_it(tmp_path: Path) -> None:
    """07:30:00 is saved without a fraction, yet still sorts before 07:30:00.000005."""
    repository = SqliteTake5Repository(tmp_path / "take5.sqlite3")
    on_the_second: SavedTake5 = sample_saved_take5()
    just_after: SavedTake5 = sample_saved_take5().model_copy(
        update={"created_at": on_the_second.created_at + timedelta(microseconds=5)},
    )
    repository.add(just_after)
    repository.add(on_the_second)

    assert repository.list_newest_first() == (just_after, on_the_second)


def test_two_saved_at_the_same_moment_list_the_last_saved_first(
    tmp_path: Path,
) -> None:
    """A tie on the time keeps a fixed order, so the list never shuffles."""
    repository = SqliteTake5Repository(tmp_path / "take5.sqlite3")
    first: SavedTake5 = sample_saved_take5()
    second: SavedTake5 = sample_saved_take5()
    repository.add(first)
    repository.add(second)

    assert repository.list_newest_first() == (second, first)


def test_the_list_is_empty_before_anything_is_saved(tmp_path: Path) -> None:
    """A new database has nothing to list."""
    assert SqliteTake5Repository(tmp_path / "take5.sqlite3").list_newest_first() == ()


def test_a_page_carries_on_after_the_one_given_even_on_a_tie(tmp_path: Path) -> None:
    """`older_than` follows the list's own order, the save order breaking a tie."""
    repository = SqliteTake5Repository(tmp_path / "take5.sqlite3")
    oldest: SavedTake5 = sample_saved_take5()
    tied_first_saved: SavedTake5 = sample_saved_take5().model_copy(
        update={"created_at": oldest.created_at + timedelta(hours=1)},
    )
    tied_last_saved: SavedTake5 = tied_first_saved.model_copy(update={"id": uuid4()})
    for take5 in (oldest, tied_first_saved, tied_last_saved):
        repository.add(take5)

    assert repository.list_newest_first(limit=1) == (tied_last_saved,)
    assert repository.list_newest_first(older_than=tied_last_saved.id, limit=1) == (
        tied_first_saved,
    )
    assert repository.list_newest_first(older_than=tied_first_saved.id) == (oldest,)
    assert repository.list_newest_first(older_than=oldest.id) == ()


def test_nothing_is_listed_after_a_take5_that_is_not_saved(tmp_path: Path) -> None:
    """An unknown `older_than` gives an empty page, not the whole list."""
    repository = SqliteTake5Repository(tmp_path / "take5.sqlite3")
    repository.add(sample_saved_take5())

    assert repository.list_newest_first(older_than=uuid4()) == ()


def test_the_fixed_ones_are_found_among_the_ids_given(tmp_path: Path) -> None:
    """`fixed_among` reads `fixes` from every saved document, not only those given."""
    repository = SqliteTake5Repository(tmp_path / "take5.sqlite3")
    fixed: SavedTake5 = sample_saved_take5()
    not_fixed: SavedTake5 = sample_saved_take5()
    fix: SavedTake5 = sample_saved_take5().model_copy(update={"fixes": fixed.id})
    for take5 in (fixed, not_fixed, fix):
        repository.add(take5)

    assert repository.fixed_among([fixed.id, not_fixed.id]) == {fixed.id}
    assert repository.fixed_among([not_fixed.id]) == frozenset()
    assert repository.fixed_among([]) == frozenset()


def _unfinished(take5: SavedTake5) -> SavedTake5:
    """Make a saved Take 5 unfinished, as one is before its question is answered.

    Args:
        take5: A finished Take 5.

    Returns:
        The same Take 5 with no verdict, no finish time and no question.
    """
    return take5.model_copy(
        update={"verdict": None, "finished_at": None, "challenge": None},
    )


ASKED: Challenge = Challenge(question="What holds the tray up?", asked_by=AskedBy.AI)
OTHER_QUESTION: Challenge = ASKED.model_copy(update={"question": "Who checked it?"})


def test_a_question_is_saved_once_on_an_unfinished_take5(tmp_path: Path) -> None:
    """The first question stays; a second one is ignored (spec C6)."""
    repository = SqliteTake5Repository(tmp_path / "take5.sqlite3")
    unfinished: SavedTake5 = repository.add(_unfinished(sample_saved_take5()))
    asked: SavedTake5 = unfinished.model_copy(update={"challenge": ASKED})

    assert repository.save_question(asked) == asked
    assert (
        repository.save_question(
            unfinished.model_copy(update={"challenge": OTHER_QUESTION}),
        )
        == asked
    )
    assert repository.get(unfinished.id) == asked


def test_a_take5_is_finished_once_and_then_never_changed(tmp_path: Path) -> None:
    """The first finish wins; neither a second finish nor a question changes it."""
    repository = SqliteTake5Repository(tmp_path / "take5.sqlite3")
    finished: SavedTake5 = sample_saved_take5().model_copy(
        update={"challenge": ASKED.model_copy(update={"answer": "Two props, checked"})},
    )
    unfinished: SavedTake5 = repository.add(_unfinished(finished))

    assert repository.finish(finished) == finished
    assert repository.finish(unfinished) == finished
    assert repository.save_question(unfinished) == finished
    assert repository.get(finished.id) == finished
