"""Tests for plugging the AI named in the settings into the app."""

import logging
from pathlib import Path

import pytest
from pydantic import SecretStr

from risk_assessment.ai.challenge import AiChallengeAsker
from risk_assessment.api.app import build_challenge_asker, create_app
from risk_assessment.services.ports import ChallengeAsker
from risk_assessment.settings import Settings
from risk_assessment.storage.sqlite import SqliteTake5Repository


def test_with_no_key_no_ai_is_plugged_in() -> None:
    """No key means no asker, so the fixed question is asked (spec C3)."""
    assert build_challenge_asker(Settings(ai_key=None)) is None


def test_with_a_key_the_ai_asks_the_question() -> None:
    """A key plugs in the provider named in the settings. Nothing is sent yet."""
    asker: ChallengeAsker | None = build_challenge_asker(
        Settings(ai_key=SecretStr("made-up-key")),
    )

    assert isinstance(asker, AiChallengeAsker)


def test_the_log_names_the_model_that_asks(caplog: pytest.LogCaptureFixture) -> None:
    """With a key, one info line says which model writes the question."""
    with caplog.at_level(logging.INFO, logger="risk_assessment"):
        build_challenge_asker(
            Settings(ai_key=SecretStr("made-up-key"), ai_model="claude-haiku-5-5"),
        )

    assert "The challenge question is asked of claude-haiku-5-5." in caplog.messages


def test_the_server_log_shows_which_model_asks(tmp_path: Path) -> None:
    """The app's info lines reach the log, so a developer sees the AI is on."""
    create_app(SqliteTake5Repository(tmp_path / "take5.sqlite3"))

    assert logging.getLogger("risk_assessment").isEnabledFor(logging.INFO)
    assert logging.getLogger("risk_assessment").handlers
