"""Nudge a vague hazard linked to a Yes to say what could hurt and where (spec T6).

An AI judges whether a hazard is vague when one is set up (task 0027). Everything here
is the part that never needs one: which hazards are judged, the text the AI is given
about one, the check on its one-word reply, and the word rule that decides whenever
the AI can't. The nudge's words are always the app's own (decision D58).
"""

import json
from collections.abc import Mapping
from enum import StrEnum
from typing import ClassVar

from pydantic import BaseModel, ConfigDict

from risk_assessment.domain.questions import Answer, Question, QuestionRole
from risk_assessment.domain.take5.draft import HazardDraft, Take5Draft
from risk_assessment.domain.take5.template import Take5Template
from risk_assessment.domain.take5.thinking import (
    hazard_wording_nudge,
    specific_hazard_message,
)
from risk_assessment.domain.wording import word_count

HAZARD_AI_TIME_LIMIT_SECONDS: float = 5
# Shown on the hazard check page when an AI judges hazards (decision D63). It names
# what `hazard_judgement_text()` sends, so the two must change together.
HAZARD_AI_NOTICE: str = (
    "The hazards you link to a Yes are checked by an AI. Your name isn't sent."
)


class HazardVerdict(StrEnum):
    """Whether a hazard says what could hurt someone, and where."""

    VAGUE = "vague"
    SPECIFIC = "specific"


class Nudge(BaseModel):
    """A suggestion to look again at an answer. It never stops submitting.

    Attributes:
        path: The answer's dotted field path, such as `hazards.0.description`.
        message: The suggestion, in plain words.
        question_id: The question to show it under, such as `vehicles`, so the phone
            needn't work out where it goes.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    path: str
    message: str
    question_id: str


class HazardToJudge(BaseModel):
    """A hazard that T6 judges, and the question its nudge would show under.

    Attributes:
        index: Where the hazard is on the worker's list, counting from 0.
        description: The hazard in the worker's own words.
        question: The first question, in the card's order, that the hazard is linked
            to and that is answered Yes.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    index: int
    description: str
    question: Question


def hazards_to_judge(
    draft: Take5Draft,
    template: Take5Template,
) -> tuple[HazardToJudge, ...]:
    """Pick the hazards T6 judges: each one not blank and linked to a question's Yes.

    A blank hazard already has its own error, and a template with no word minimum
    turns T6 off, so neither is judged or sent to an AI (decision D60).

    Args:
        draft: The worker's answers so far.
        template: The template the draft is filled in on.

    Returns:
        The hazards to judge, in the order of the list.
    """
    if template.specific_hazard_words is None:
        return ()
    judged: list[HazardToJudge] = []
    for index, hazard in enumerate(draft.hazards):
        question: Question | None = _first_linked_yes(hazard, draft, template)
        if question is not None and word_count(hazard.description) > 0:
            judged.append(
                HazardToJudge(
                    index=index,
                    description=hazard.description,
                    question=question,
                ),
            )
    return tuple(judged)


def _first_linked_yes(
    hazard: HazardDraft,
    draft: Take5Draft,
    template: Take5Template,
) -> Question | None:
    """Find the first hazard question, in the card's order, linked to it and a Yes.

    Args:
        hazard: One hazard on the worker's list.
        draft: The worker's answers so far.
        template: The template the draft is filled in on.

    Returns:
        The question, or None when the hazard is linked to no Yes.
    """
    return next(
        (
            question
            for question in template.questions
            if question.role is QuestionRole.HAZARD
            and question.id in hazard.covers
            and draft.answers.get(question.id) is Answer.YES
        ),
        None,
    )


def hazard_judgement_text(hazard: HazardToJudge, job: str, location: str) -> str:
    """Write out what the AI is given about one hazard (spec T6).

    It is JSON, so everything the worker typed sits inside a quoted value. A hazard that
    says "ignore your instructions" stays a hazard, and the AI's instructions can say to
    treat all of it as data. The worker's name is not a parameter, so it can't be sent.
    The same text is the key the AI's answer is remembered by (decision D59).

    Args:
        hazard: The hazard, with the question it is linked to.
        job: What the job is, in the worker's words.
        location: Where the job is.

    Returns:
        The hazard, the card's question, the job and where it is.
    """
    described: dict[str, str] = {
        "hazard": hazard.description,
        "card_question": hazard.question.text,
        "job": job,
        "location": location,
    }
    return json.dumps(described, indent=2, ensure_ascii=False)


def hazard_verdict(reply: str) -> HazardVerdict | None:
    """Read the AI's one-word reply, ignoring spaces, capitals and a closing full stop.

    Args:
        reply: The AI's reply, exactly as it came.

    Returns:
        The verdict, or None when the reply is anything but "vague" or "specific", so
        the word rule decides instead.
    """
    word: str = reply.strip().removesuffix(".").lower()
    try:
        return HazardVerdict(word)
    except ValueError:
        return None


def specific_hazard_nudges(
    draft: Take5Draft,
    template: Take5Template,
    ai_verdicts: Mapping[int, HazardVerdict],
) -> tuple[Nudge, ...]:
    """Nudge each vague hazard linked to a Yes to say what could hurt and where (T6).

    The AI's verdict decides where there is one. For any hazard it didn't judge in time,
    the word rule decides: fewer words than the template's minimum is vague.

    Args:
        draft: The worker's answers so far.
        template: The template the draft is filled in on.
        ai_verdicts: The AI's verdict on each hazard it judged, by its place on the
            list. Empty when no AI is set up.

    Returns:
        One nudge on each vague hazard's `description` path, in the order of the list,
        under the first question it is linked to that is answered Yes.
    """
    return tuple(
        Nudge(
            path=f"hazards.{hazard.index}.description",
            message=specific_hazard_message(hazard.question.example),
            question_id=hazard.question.id,
        )
        for hazard in hazards_to_judge(draft, template)
        if _is_vague(hazard, ai_verdicts.get(hazard.index), template)
    )


def _is_vague(
    hazard: HazardToJudge,
    ai_verdict: HazardVerdict | None,
    template: Take5Template,
) -> bool:
    """Decide whether one hazard is vague: by the AI's verdict, or else the word rule.

    Args:
        hazard: The hazard being judged.
        ai_verdict: What the AI decided, or None when it didn't judge this hazard.
        template: The template, for its word minimum.

    Returns:
        True when the hazard should be nudged.
    """
    if ai_verdict is not None:
        return ai_verdict is HazardVerdict.VAGUE
    return (
        hazard_wording_nudge(hazard.description, "", template.specific_hazard_words)
        is not None
    )
