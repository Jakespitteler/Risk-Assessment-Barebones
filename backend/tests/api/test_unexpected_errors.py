"""Tests that a bug in a route names its request above the trace (task 0028)."""

import logging
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from risk_assessment.api.app import create_app
from risk_assessment.storage.sqlite import SqliteTake5Repository


def test_a_bug_in_a_route_names_the_request_and_replies_a_plain_500(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """One error line gives the method and path, never the body; the reply is plain."""
    app = create_app(SqliteTake5Repository(tmp_path / "take5.sqlite3"))

    @app.post("/api/broken")
    def broken() -> None:  # pyright: ignore[reportUnusedFunction]
        """A route with a bug in it."""
        raise RuntimeError("a bug")

    with caplog.at_level(logging.ERROR, logger="risk_assessment"):
        response = TestClient(app, raise_server_exceptions=False).post(
            "/api/broken",
            json={"worker_name": "Sam Example"},
        )

    (line,) = [record for record in caplog.records if record.name.endswith("errors")]
    assert line.getMessage() == (
        "POST /api/broken failed with an unexpected error; its trace follows."
    )
    assert "Sam Example" not in caplog.text
    assert response.status_code == 500
    assert response.text == "Internal Server Error"
