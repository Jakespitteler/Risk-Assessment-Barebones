"""SQLite storage for whole immutable Take 5 documents."""

import sqlite3
from contextlib import closing
from pathlib import Path
from uuid import UUID

from risk_assessment.domain.take5.saved import SavedTake5


class SqliteTake5Repository:
    """Keep each assessment as JSON beside the columns needed for a later list."""

    def __init__(self, database_path: Path) -> None:
        """Remember the path without opening a database during API type generation."""
        self._database_path: Path = database_path

    def _connect(self) -> sqlite3.Connection:
        """Open a short-lived connection and prepare the documented table if needed."""
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        connection: sqlite3.Connection = sqlite3.connect(self._database_path)
        connection.execute(
            "CREATE TABLE IF NOT EXISTS take5s (id TEXT PRIMARY KEY, created_at TEXT, "
            "worker_name TEXT, job TEXT, document TEXT NOT NULL)"
        )
        return connection

    def add(self, take5: SavedTake5) -> SavedTake5:
        """Insert atomically; a repeated ID cannot replace a finished assessment."""
        with closing(self._connect()) as connection, connection:
            connection.execute(
                "INSERT INTO take5s VALUES (?, ?, ?, ?, ?) ON CONFLICT(id) DO NOTHING",
                (
                    str(take5.id),
                    take5.created_at.isoformat(),
                    take5.worker_name,
                    take5.job,
                    take5.model_dump_json(),
                ),
            )
            row: tuple[str] | None = connection.execute(
                "SELECT document FROM take5s WHERE id = ?", (str(take5.id),)
            ).fetchone()
        assert row is not None
        return SavedTake5.model_validate_json(row[0])

    def get(self, take5_id: UUID) -> SavedTake5 | None:
        """Read the original template and verdict from the stored document."""
        with closing(self._connect()) as connection:
            row: tuple[str] | None = connection.execute(
                "SELECT document FROM take5s WHERE id = ?", (str(take5_id),)
            ).fetchone()
        return SavedTake5.model_validate_json(row[0]) if row else None
