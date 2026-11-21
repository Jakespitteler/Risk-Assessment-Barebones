"""Calls to the real Claude, run only when a key is set. Never runs in CI.

Run it with `uv run pytest -m real_ai` after putting `TAKE5_AI_KEY` in `backend/.env`.
"""

import pytest

from risk_assessment.ai.challenge import AiChallengeAsker
from risk_assessment.ai.providers.claude import QUICK_MODEL, ClaudeModel
from risk_assessment.ai.vague_hazard import AiHazardJudge
from risk_assessment.domain.questions import Question
from risk_assessment.domain.take5.challenge import (
    AiQuestion,
    challenge_text,
    checked_question,
)
from risk_assessment.domain.take5.hazard_nudges import (
    HazardToJudge,
    hazard_judgement_text,
    hazard_verdict,
)
from risk_assessment.domain.take5.saved import SavedTake5
from risk_assessment.domain.take5.template import BOOKLET_TEMPLATE
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


def test_the_real_claude_judges_a_hazard_with_one_of_the_four_words() -> None:
    """Claude's reply about a sample hazard is one of the four words (D58, D105)."""
    key: str = _settings.usable_ai_key or ""
    vehicles: Question = next(
        question for question in BOOKLET_TEMPLATE.questions if question.id == "vehicles"
    )
    hazard = HazardToJudge(index=0, description="Get hit by a car", question=vehicles)
    judge = AiHazardJudge(ClaudeModel(key, _settings.ai_hazard_model or QUICK_MODEL))

    reply: str = judge.judge(
        hazard_judgement_text(
            hazard,
            "Survey the pegs along the haul road",
            "South pit",
        ),
    )

    assert hazard_verdict(reply) is not None, reply
