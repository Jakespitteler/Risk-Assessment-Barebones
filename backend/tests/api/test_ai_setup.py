"""Tests for plugging the AI named in the settings into the app."""

import logging
from pathlib import Path

from pydantic import SecretStr

from risk_assessment.ai.challenge import AiChallengeAsker
from risk_assessment.ai.vague_hazard import AiHazardJudge
from risk_assessment.api.app import (
    build_challenge_asker,
    build_hazard_judge,
    create_app,
)
from risk_assessment.services.ports import ChallengeAsker, HazardJudge
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


def test_with_no_key_the_word_rule_judges_hazards() -> None:
    """No key means no judge, so the word rule decides (spec T6)."""
    assert build_hazard_judge(Settings(ai_key=None)) is None


def test_hazards_are_judged_by_the_providers_quick_model() -> None:
    """With no hazard model set, Claude Haiku 5.5 judges hazards (decision D61)."""
    judge: HazardJudge | None = build_hazard_judge(
        Settings(ai_key=SecretStr("made-up-key"), ai_model="claude-opus-5-5"),
    )

    assert isinstance(judge, AiHazardJudge)
    assert judge.model_name == "claude-haiku-5-5"


def test_the_hazard_model_is_a_setting() -> None:
    """`TAKE5_AI_HAZARD_MODEL` picks another model for this job only."""
    judge: HazardJudge | None = build_hazard_judge(
        Settings(
            ai_key=SecretStr("made-up-key"),
            ai_hazard_model="claude-sonnet-5-5",
        ),
    )

    assert isinstance(judge, AiHazardJudge)
    assert judge.model_name == "claude-sonnet-5-5"


def test_the_server_log_shows_which_model_asks(tmp_path: Path) -> None:
    """The app's info lines reach the log, so a developer sees the AI is on."""
    create_app(SqliteTake5Repository(tmp_path / "take5.sqlite3"))

    assert logging.getLogger("risk_assessment").isEnabledFor(logging.INFO)
    assert logging.getLogger("risk_assessment").handlers
