"""Tests for reading the settings from the environment."""

from pathlib import Path

import pytest

from risk_assessment.settings import Settings


def test_the_database_is_in_the_ignored_data_folder_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With nothing set, the database is `backend/.data/take5.sqlite3`."""
    monkeypatch.delenv("TAKE5_DATABASE_PATH", raising=False)

    database_path: Path = Settings().database_path

    assert database_path.parts[-3:] == ("backend", ".data", "take5.sqlite3")


def test_the_database_path_can_be_set_from_the_environment(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """`TAKE5_DATABASE_PATH` moves the database."""
    monkeypatch.setenv("TAKE5_DATABASE_PATH", str(tmp_path / "other.sqlite3"))

    assert Settings().database_path == tmp_path / "other.sqlite3"
