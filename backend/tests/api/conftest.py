"""Set-up shared by the API tests."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from risk_assessment.api.app import create_app
from risk_assessment.storage.sqlite import SqliteTake5Repository


@pytest.fixture
def repository(tmp_path: Path) -> SqliteTake5Repository:
    """Give each test its own empty SQLite database in a temporary folder.

    Args:
        tmp_path: pytest's temporary folder for this test.

    Returns:
        The repository. Nothing is written to disk until a Take 5 is saved.
    """
    return SqliteTake5Repository(tmp_path / "take5.sqlite3")


@pytest.fixture
def client(repository: SqliteTake5Repository) -> TestClient:
    """Give each test the real app, talking to the test's own `repository`.

    A test that also asks for `repository` gets the same one, so it can look at what
    was saved.

    Args:
        repository: The test's empty SQLite repository.

    Returns:
        A test client that sends requests to the app without a server.
    """
    return TestClient(create_app(repository))
