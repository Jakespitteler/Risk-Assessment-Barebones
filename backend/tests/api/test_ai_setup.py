"""Tests for plugging the AI named in the settings into the app."""

from pydantic import SecretStr

from risk_assessment.ai.challenge import AiChallengeAsker
from risk_assessment.api.app import build_challenge_asker
from risk_assessment.services.ports import ChallengeAsker
from risk_assessment.settings import Settings


def test_with_no_key_no_ai_is_plugged_in() -> None:
    """No key means no asker, so the fixed question is asked (spec C3)."""
    assert build_challenge_asker(Settings(ai_key=None)) is None


def test_with_a_key_the_ai_asks_the_question() -> None:
    """A key plugs in the provider named in the settings. Nothing is sent yet."""
    asker: ChallengeAsker | None = build_challenge_asker(
        Settings(ai_key=SecretStr("made-up-key")),
    )

    assert isinstance(asker, AiChallengeAsker)
