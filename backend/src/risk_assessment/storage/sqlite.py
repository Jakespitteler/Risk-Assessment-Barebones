"""SQLite storage: each Take 5 is kept whole, as one JSON document."""

import sqlite3
from collections.abc import Collection
from contextlib import closing
from pathlib import Path
from uuid import UUID

from risk_assessment.domain.take5.saved import SavedTake5

# The one table, as docs/architecture.md describes it.
_CREATE_TABLE: str = (
    "CREATE TABLE IF NOT EXISTS take5s ("
    "id TEXT PRIMARY KEY, created_at TEXT, worker_name TEXT, job TEXT, "
    "document TEXT NOT NULL)"
)
_INSERT: str = (
    "INSERT INTO take5s (id, created_at, worker_name, job, document) "
    "VALUES (?, ?, ?, ?, ?) ON CONFLICT(id) DO NOTHING"
)
_SELECT_DOCUMENT: str = "SELECT document FROM take5s WHERE id = ?"
# An unfinished Take 5 has no verdict. These only change a row that is still
# unfinished, so a finished Take 5 is never written to again, and the first of two
# requests at once wins. A Take 5's question is added once, so its question stays put.
_SAVE_QUESTION: str = (
    "UPDATE take5s SET document = ? WHERE id = ? "
    "AND json_extract(document, '$.verdict') IS NULL "
    "AND json_extract(document, '$.challenge') IS NULL"
)
_FINISH: str = (
    "UPDATE take5s SET document = ? WHERE id = ? "
    "AND json_extract(document, '$.verdict') IS NULL"
)
# The service saves every time in UTC, and ISO text in one time zone sorts by time.
# A time with no fraction of a second, such as 07:30:00+00:00, still sorts before
# 07:30:00.000005+00:00, because "+" sorts before ".". The row ID breaks a tie, so
# the one saved last comes first.
# "Older than" compares the same pair the list is sorted by, so a page carries on
# exactly where the last one stopped. LIMIT -1 means no limit.
_SELECT_NEWEST_FIRST: str = (
    "SELECT document FROM take5s ORDER BY created_at DESC, rowid DESC LIMIT ?"
)
_SELECT_OLDER_THAN: str = (
    "SELECT document FROM take5s "
    "WHERE (created_at, rowid) < (SELECT created_at, rowid FROM take5s WHERE id = ?) "
    "ORDER BY created_at DESC, rowid DESC LIMIT ?"
)
_NO_LIMIT: int = -1
# A fix points back at the Take 5 it fixes from inside its own document, so the first
# one is never written to again. The newest fix wins if there is more than one.
_SELECT_NEWEST_FIX: str = (
    "SELECT id FROM take5s WHERE json_extract(document, '$.fixes') = ? "
    "ORDER BY created_at DESC, rowid DESC LIMIT 1"
)


class SqliteTake5Repository:
    """Keeps each Take 5 as JSON, with a few columns beside it for sorting."""

    def __init__(self, database_path: Path) -> None:
        """Remember where the file is, without opening it yet.

        The file is opened on first use, so writing the API description for the front
        end never creates a database.

        Args:
            database_path: The SQLite file. Its folder is made if it doesn't exist.
        """
        self._database_path: Path = database_path
        self._table_ready: bool = False

    def add(self, take5: SavedTake5) -> SavedTake5:
        """Save a Take 5, unless one with the same ID is already saved.

        Two requests at once with the same ID can't both save: the first one wins.

        Args:
            take5: The Take 5 to save.

        Returns:
            The Take 5 now saved with this ID: this one, or the one saved first.

        Raises:
            LookupError: If the Take 5 can't be read back after saving.
        """
        with closing(self._connect()) as connection, connection:
            connection.execute(
                _INSERT,
                (
                    str(take5.id),
                    take5.created_at.isoformat(),
                    take5.worker_name,
                    take5.job,
                    take5.model_dump_json(),
                ),
            )
            stored: SavedTake5 | None = _read(connection, take5.id)
        if stored is None:
            raise LookupError(f"Take 5 {take5.id} was not saved.")
        return stored

    def save_question(self, take5: SavedTake5) -> SavedTake5:
        """Replace an unfinished Take 5 that has no question yet with this one.

        Args:
            take5: The Take 5 with its question added.

        Returns:
            The Take 5 now saved with this ID: this one, or the one already there if
            it had a question or was finished.
        """
        return self._update(_SAVE_QUESTION, take5)

    def finish(self, take5: SavedTake5) -> SavedTake5:
        """Replace an unfinished Take 5 with this finished one.

        Args:
            take5: The Take 5 with its answer, verdict and `finished_at`.

        Returns:
            The Take 5 now saved with this ID: this one, or the one already there if
            it was finished first.
        """
        return self._update(_FINISH, take5)

    def get(self, take5_id: UUID) -> SavedTake5 | None:
        """Get a saved Take 5, with the template and verdict it was saved with.

        Args:
            take5_id: The Take 5's ID.

        Returns:
            The saved Take 5, or None if there is none with this ID.
        """
        with closing(self._connect()) as connection:
            return _read(connection, take5_id)

    def list_newest_first(
        self,
        older_than: UUID | None = None,
        limit: int | None = None,
    ) -> tuple[SavedTake5, ...]:
        """Get saved Take 5s, the newest first.

        Args:
            older_than: Only those listed after this Take 5, or None to start at the
                newest. None are listed after a Take 5 that isn't saved.
            limit: At most this many, or None for all of them.

        Returns:
            The saved Take 5s, each with the template and verdict it was saved with.
        """
        row_limit: int = _NO_LIMIT if limit is None else limit
        with closing(self._connect()) as connection:
            rows: list[tuple[str]] = (
                connection.execute(_SELECT_NEWEST_FIRST, (row_limit,)).fetchall()
                if older_than is None
                else connection.execute(
                    _SELECT_OLDER_THAN,
                    (str(older_than), row_limit),
                ).fetchall()
            )
        return tuple(SavedTake5.model_validate_json(document) for (document,) in rows)

    def fixed_among(self, take5_ids: Collection[UUID]) -> frozenset[UUID]:
        """Find which of these Take 5s a saved Take 5 fixes.

        Args:
            take5_ids: The IDs to look for.

        Returns:
            The ones some saved Take 5 points back at with `fixes`.
        """
        if not take5_ids:
            return frozenset()
        placeholders: str = ", ".join("?" for _ in take5_ids)
        with closing(self._connect()) as connection:
            rows: list[tuple[str]] = connection.execute(
                "SELECT DISTINCT json_extract(document, '$.fixes') FROM take5s "
                f"WHERE json_extract(document, '$.fixes') IN ({placeholders})",
                tuple(str(take5_id) for take5_id in take5_ids),
            ).fetchall()
        return frozenset(UUID(fixed_id) for (fixed_id,) in rows)

    def fixed_by(self, take5_id: UUID) -> UUID | None:
        """Find the newest saved Take 5 that fixes this one.

        Args:
            take5_id: The ID of the Take 5 that may have been fixed.

        Returns:
            The newest fix's ID, or None if there is none.
        """
        with closing(self._connect()) as connection:
            row: tuple[str] | None = connection.execute(
                _SELECT_NEWEST_FIX,
                (str(take5_id),),
            ).fetchone()
        return UUID(row[0]) if row is not None else None

    def _update(self, statement: str, take5: SavedTake5) -> SavedTake5:
        """Run one guarded update of a Take 5's document, then read back what is saved.

        Args:
            statement: The UPDATE to run, which says when the row may change.
            take5: The new document.

        Returns:
            The Take 5 now saved with this ID.

        Raises:
            LookupError: If no Take 5 is saved with this ID.
        """
        with closing(self._connect()) as connection, connection:
            connection.execute(statement, (take5.model_dump_json(), str(take5.id)))
            stored: SavedTake5 | None = _read(connection, take5.id)
        if stored is None:
            raise LookupError(f"Take 5 {take5.id} is not saved.")
        return stored

    def _connect(self) -> sqlite3.Connection:
        """Open a short-lived connection, making the file and table on first use.

        Returns:
            An open connection, which the caller closes.
        """
        if not self._table_ready:
            self._database_path.parent.mkdir(parents=True, exist_ok=True)
        connection: sqlite3.Connection = sqlite3.connect(self._database_path)
        if not self._table_ready:
            with connection:
                connection.execute(_CREATE_TABLE)
            self._table_ready = True
        return connection


def _read(connection: sqlite3.Connection, take5_id: UUID) -> SavedTake5 | None:
    """Read one Take 5's document.

    Args:
        connection: An open connection.
        take5_id: The Take 5's ID.

    Returns:
        The saved Take 5, or None if there is none with this ID.
    """
    row: tuple[str] | None = connection.execute(
        _SELECT_DOCUMENT,
        (str(take5_id),),
    ).fetchone()
    return SavedTake5.model_validate_json(row[0]) if row is not None else None
