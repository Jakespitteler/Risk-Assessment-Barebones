"""The one question asked before the result (spec C1 to C6).

An AI writes the question when it can. Everything here is the part that never needs
one: the text the AI is given, the check on what it sends back, the fixed question
asked when it can't, and the check on the worker's answer. The AI only asks; nothing
here, and nothing it writes, decides whether anyone can start work.
"""

import json
from enum import StrEnum
from typing import ClassVar

from pydantic import BaseModel, ConfigDict

from risk_assessment.domain.risk import RiskRating
from risk_assessment.domain.take5.draft import FieldError
from risk_assessment.domain.take5.take5 import Hazard, Take5
from risk_assessment.domain.wording import word_count

ANSWER_PATH: str = "answer"
QUESTION_MAX_CHARACTERS: int = 300
ANSWER_MIN_WORDS: int = 4
AI_TIME_LIMIT_SECONDS: float = 10
SHORT_ANSWER_MESSAGE: str = (
    "Answer in at least four words: say what you'll check or do."
)


class AskedBy(StrEnum):
    """Who wrote the question the worker was asked."""

    AI = "ai"
    FALLBACK = "fallback"


class AiQuestion(BaseModel):
    """What an AI sent back, before it is checked (spec C2).

    Attributes:
        text: The AI's reply, exactly as it came.
        model: Which model wrote it, such as the provider's model name.
        instructions_version: Which version of its instructions it was given.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    text: str
    model: str
    instructions_version: str


class Challenge(BaseModel):
    """The question a Take 5 was asked, who asked it, and the worker's answer.

    Attributes:
        question: The question the worker was shown.
        asked_by: Whether the AI or the fallback asked it.
        model: For an AI question, which model asked it. None for the fallback.
        instructions_version: For an AI question, which version of its instructions
            it had. None for the fallback.
        answer: The worker's answer, or None until they give one.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    question: str
    asked_by: AskedBy
    model: str | None = None
    instructions_version: str | None = None
    answer: str | None = None


def challenge_text(take5: Take5, job: str, location: str) -> str:
    """Write out what the AI is given about a Take 5 (spec C1).

    It is JSON, so everything the worker typed sits inside a quoted value. A job that
    says "ignore your instructions" stays a job, and the AI's instructions can say to
    treat all of it as data. The worker's name is not a parameter, so it can't be sent.

    Args:
        take5: The rated Take 5, with its template, answers and hazards.
        job: What the job is, in the worker's words.
        location: Where the job is.

    Returns:
        The job, where it is, each question with its answer, and each hazard with its
        ratings, controls and the questions it is linked to.
    """
    question_text: dict[str, str] = {
        question.id: question.text for question in take5.template.questions
    }
    described: dict[str, object] = {
        "job": job,
        "location": location,
        "answers": [
            {"question": question_text[question_id], "answer": answer.value}
            for question_id, answer in take5.answers.items()
        ],
        "hazards": [
            _described_hazard(hazard, question_text) for hazard in take5.hazards
        ],
    }
    return json.dumps(described, indent=2, ensure_ascii=False)


def _described_hazard(
    hazard: Hazard,
    question_text: dict[str, str],
) -> dict[str, object]:
    """Write out one hazard for the AI.

    Args:
        hazard: The rated hazard.
        question_text: Each question's wording, by its ID.

    Returns:
        The hazard's description, ratings, controls, linked questions and, when T3
        asked, why no strong control is possible.
    """
    described: dict[str, object] = {
        "description": hazard.description,
        "before_controls": _described_rating(hazard.before),
        "controls": [
            {"description": control.description, "kind": control.kind.value}
            for control in hazard.controls
        ],
        "after_controls": _described_rating(hazard.after),
        "linked_to_questions": [
            question_text[question_id] for question_id in hazard.covers
        ],
    }
    if hazard.weak_controls_reason:
        described["why_no_strong_control"] = hazard.weak_controls_reason
    return described


def _described_rating(rating: RiskRating) -> str:
    """Write a rating the way the card says it.

    Args:
        rating: A rating from the matrix.

    Returns:
        Such as "Possible / Major: 18 Extreme".
    """
    return f"{rating.likelihood} / {rating.consequence}: {rating.score} {rating.band}"


def checked_question(reply: str) -> str | None:
    """Keep the AI's reply only if it is one short question (spec C2).

    Args:
        reply: The AI's reply, exactly as it came.

    Returns:
        The reply without spaces and line breaks at its ends, or None when what is
        left is longer than 300 characters or doesn't end with a question mark.
    """
    question: str = reply.strip()
    if len(question) > QUESTION_MAX_CHARACTERS or not question.endswith("?"):
        return None
    return question


def ai_challenge(reply: AiQuestion) -> Challenge | None:
    """Turn an AI's reply into the question to ask, if it passes C2.

    Args:
        reply: What the AI sent back.

    Returns:
        The question, recorded as asked by that model, or None when C2 throws it
        away.
    """
    question: str | None = checked_question(reply.text)
    if question is None:
        return None
    return Challenge(
        question=question,
        asked_by=AskedBy.AI,
        model=reply.model,
        instructions_version=reply.instructions_version,
    )


def fallback_challenge(take5: Take5) -> Challenge:
    """Ask the fixed question about the hazard with the highest before rating (C3).

    Args:
        take5: The rated Take 5. It always has at least one hazard.

    Returns:
        The fixed question about the first hazard with the highest before score.
    """
    riskiest: Hazard = max(take5.hazards, key=lambda hazard: hazard.before.score)
    return Challenge(
        question=(
            "What is the one thing that has to go right so that "
            f"'{riskiest.description}' doesn't hurt anyone, and how will you check "
            "it before you start?"
        ),
        asked_by=AskedBy.FALLBACK,
    )


def answer_error(answer: str) -> FieldError | None:
    """Say why an answer is too short, if it is (spec C4).

    Args:
        answer: The worker's answer.

    Returns:
        The error to show beside the answer, or None when it has at least four words.
    """
    if word_count(answer) >= ANSWER_MIN_WORDS:
        return None
    return FieldError(path=ANSWER_PATH, message=SHORT_ANSWER_MESSAGE)
