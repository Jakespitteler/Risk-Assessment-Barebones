"""Tests for reading a photo of a paper card through the API (task 0033)."""

from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from risk_assessment.api.app import create_app
from risk_assessment.services.card_scanning import (
    MAX_PHOTO_BYTES,
    NO_AI_MESSAGE,
    TOO_BIG_MESSAGE,
    UNREADABLE_MESSAGE,
    WRONG_TYPE_MESSAGE,
)
from risk_assessment.storage.sqlite import SqliteTake5Repository
from tests.services.test_card_scanning import StandInReader


def client_with(tmp_path: Path, reader: StandInReader | None) -> TestClient:
    """Make the API with a stand-in for the AI that reads cards, and no AI key.

    Args:
        tmp_path: pytest's temporary folder for this test.
        reader: The stand-in, or None for no AI set up.

    Returns:
        A test client.
    """
    repository = SqliteTake5Repository(tmp_path / "take5.sqlite3")
    return TestClient(create_app(repository, card_reader=reader))


def test_a_photo_comes_back_as_a_card_to_check_and_nothing_is_saved(
    tmp_path: Path,
) -> None:
    """The reply holds the draft as read; the saved list stays empty."""
    client: TestClient = client_with(tmp_path, StandInReader())

    response = client.post(
        "/api/scans",
        files={"photo": ("card.jpg", b"photo bytes", "image/jpeg")},
    )

    body: dict[str, Any] = response.json()
    assert response.status_code == 200
    assert body["draft"]["job"] == "Change the front left tyre on LV12"
    assert body["unreadable"] == []
    assert client.get("/api/take5s").json()["take5s"] == []


def test_with_no_ai_the_reply_is_a_503_saying_so(tmp_path: Path) -> None:
    """Never an AI error: a plain message the page can show."""
    response = client_with(tmp_path, None).post(
        "/api/scans",
        files={"photo": ("card.jpg", b"photo bytes", "image/jpeg")},
    )

    assert response.status_code == 503
    assert response.json() == {"detail": NO_AI_MESSAGE}


def test_a_file_that_is_not_a_photo_is_a_422_beside_the_photo(tmp_path: Path) -> None:
    """The message sits on the `photo` field, in the API's one 422 shape."""
    response = client_with(tmp_path, StandInReader()).post(
        "/api/scans",
        files={"photo": ("card.pdf", b"%PDF", "application/pdf")},
    )

    assert response.status_code == 422
    assert response.json()["errors"] == [
        {"path": "photo", "message": WRONG_TYPE_MESSAGE},
    ]


def test_a_too_big_upload_is_a_422_beside_the_photo(tmp_path: Path) -> None:
    """The route reads one byte past the limit, so a big photo is refused."""
    response = client_with(tmp_path, StandInReader()).post(
        "/api/scans",
        files={"photo": ("card.jpg", b"x" * (MAX_PHOTO_BYTES + 1), "image/jpeg")},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == TOO_BIG_MESSAGE


def test_a_type_in_capitals_or_with_extras_is_still_a_photo(tmp_path: Path) -> None:
    """A type such as "IMAGE/JPEG; charset=binary" is read as a JPEG."""
    response = client_with(tmp_path, StandInReader()).post(
        "/api/scans",
        files={"photo": ("card.jpg", b"photo", "IMAGE/JPEG; charset=binary")},
    )

    assert response.status_code == 200


def test_an_ai_failure_is_a_422_beside_the_photo_never_an_ai_error(
    tmp_path: Path,
) -> None:
    """The person is asked to retake the photo; the AI's own message never shows."""
    reader = StandInReader(failure=ConnectionError("provider says no"))

    response = client_with(tmp_path, reader).post(
        "/api/scans",
        files={"photo": ("card.jpg", b"photo", "image/jpeg")},
    )

    assert response.status_code == 422
    assert response.json()["errors"] == [
        {"path": "photo", "message": UNREADABLE_MESSAGE},
    ]
    assert "provider says no" not in response.text
