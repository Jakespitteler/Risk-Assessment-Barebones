"""One call to the real Claude, run only when a key is set. Never runs in CI.

Run it with `uv run pytest -m real_ai` after putting `TAKE5_AI_KEY` in `backend/.env`.
"""

import pytest

from risk_assessment.ai.challenge import AiChallengeAsker
from risk_assessment.ai.providers.claude import ClaudeModel
from risk_assessment.domain.take5.challenge import (
    AiQuestion,
    challenge_text,
    checked_question,
)
from risk_assessment.domain.take5.saved import SavedTake5
from risk_assessment.settings import Settings
from tests.samples import sample_saved_take5

_settings = Settings()

pytestmark = [
    pytest.mark.real_ai,
    pytest.mark.skipif(
        _settings.usable_ai_key is None,
        reason="No TAKE5_AI_KEY is set, so the real AI isn't called.",
    ),
]


def test_the_real_claude_asks_a_usable_question() -> None:
    """Claude's reply to a sample Take 5 passes the check on its question (C2)."""
    key: str = _settings.usable_ai_key or ""
    take5: SavedTake5 = sample_saved_take5()
    asker = AiChallengeAsker(ClaudeModel(key, _settings.ai_model))

    reply: AiQuestion = asker.ask(challenge_text(take5, take5.job, take5.location))

    assert checked_question(reply.text) is not None, reply.text
