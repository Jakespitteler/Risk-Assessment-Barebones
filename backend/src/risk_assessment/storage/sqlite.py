"""SQLite storage: each Take 5 is kept whole, as one JSON document."""

import sqlite3
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


class SqliteTake5Repository:
    """Keeps each Take 5 as JSON, with a few columns beside it for a later list."""

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

    def get(self, take5_id: UUID) -> SavedTake5 | None:
        """Get a saved Take 5, with the template and verdict it was saved with.

        Args:
            take5_id: The Take 5's ID.

        Returns:
            The saved Take 5, or None if there is none with this ID.
        """
        with closing(self._connect()) as connection:
            return _read(connection, take5_id)

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
        _SELECT_DOCUMENT, (str(take5_id),)
    ).fetchone()
    return SavedTake5.model_validate_json(row[0]) if row is not None else None
