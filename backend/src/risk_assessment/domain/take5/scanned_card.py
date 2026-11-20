"""A paper card as the AI read it, kept to what the template allows (task 0033).

The AI's reply is untrusted: a word the template doesn't have (an answer, a level or a
control kind) is left empty and marked unreadable, for the person checking the card to
fill in from the photo. Nothing is rewritten to pass a rule: a card is kept as written,
gaps and all.
"""

import json
from datetime import datetime
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, ValidationError

from risk_assessment.domain.controls import ControlKind
from risk_assessment.domain.questions import Answer
from risk_assessment.domain.take5.draft import (
    ControlDraft,
    HazardDraft,
    RatingChoice,
    Take5Draft,
)
from risk_assessment.domain.take5.template import Take5Template


class ScannedCard(BaseModel):
    """What the AI read off one paper card, for a person to check.

    Attributes:
        draft: The card as a draft Take 5, with the worker's name as written.
        filled_in_at: The date and time written on the card, as read, without a time
            zone unless the card gave one; None when there was none or it couldn't
            be read.
        unreadable: The paths of the fields the AI couldn't read, or wrote with a word
            the template doesn't have, such as "job" or "hazards.0.before".
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    draft: Take5Draft
    filled_in_at: datetime | None = None
    unreadable: tuple[str, ...] = ()


class _Rating(BaseModel):
    """A rating as the AI wrote it."""

    likelihood: str | None = None
    consequence: str | None = None


class _Control(BaseModel):
    """A control as the AI wrote it."""

    description: str = ""
    kind: str | None = None


class _Hazard(BaseModel):
    """A hazard as the AI wrote it."""

    description: str = ""
    before: _Rating = _Rating()
    controls: list[_Control] = []
    after: _Rating = _Rating()


class _Reply(BaseModel):
    """The AI's whole reply, before anything in it is trusted."""

    worker_name: str = ""
    job: str = ""
    location: str = ""
    filled_in_at: str | None = None
    answers: dict[str, str] = {}
    hazards: list[_Hazard] = []
    unreadable: list[str] = []


def without_fence(reply: str) -> str:
    """Take off the ```json fence a model sometimes puts round its JSON.

    Args:
        reply: The AI's reply.

    Returns:
        The reply without the fence, trimmed.
    """
    text: str = reply.strip()
    if text.startswith("```") and text.endswith("```"):
        text = text.removeprefix("```json").removeprefix("```").removesuffix("```")
    return text.strip()


def scanned_card(reply: str, template: Take5Template) -> ScannedCard | None:
    """Read the AI's reply about one card into a card to check.

    Args:
        reply: The AI's reply: one JSON object, perhaps in a code fence.
        template: The card the photo was of.

    Returns:
        The card, or None when the reply isn't the JSON asked for.
    """
    try:
        loaded: Any = json.loads(without_fence(reply))
        read: _Reply = _Reply.model_validate(loaded)
    except (json.JSONDecodeError, ValidationError):
        return None
    unreadable: list[str] = list(read.unreadable)
    answers: dict[str, Answer] = _answers(read.answers, template, unreadable)
    hazards: tuple[HazardDraft, ...] = tuple(
        _hazard(hazard, f"hazards.{index}", template, unreadable)
        for index, hazard in enumerate(read.hazards)
    )
    draft = Take5Draft(
        worker_name=read.worker_name.strip(),
        job=read.job.strip(),
        location=read.location.strip(),
        answers=answers,
        hazards=hazards,
    )
    return ScannedCard(
        draft=draft,
        filled_in_at=_date_time(read.filled_in_at, unreadable),
        unreadable=tuple(dict.fromkeys(unreadable)),
    )


def _answers(
    written: dict[str, str],
    template: Take5Template,
    unreadable: list[str],
) -> dict[str, Answer]:
    """Keep the answers to the card's own questions that are a real answer.

    Args:
        written: The answers as the AI wrote them, by question id.
        template: The card, with its question ids.
        unreadable: Paths of fields left empty, to add to.

    Returns:
        Each usable answer, by question id.
    """
    question_ids: set[str] = {question.id for question in template.questions}
    answers: dict[str, Answer] = {}
    for question_id, word in written.items():
        if question_id not in question_ids:
            continue
        if word in {answer.value for answer in Answer}:
            answers[question_id] = Answer(word)
        else:
            unreadable.append(f"answers.{question_id}")
    return answers


def _hazard(
    written: _Hazard,
    path: str,
    template: Take5Template,
    unreadable: list[str],
) -> HazardDraft:
    """Keep one hazard, with only the levels and kinds the template has.

    Args:
        written: The hazard as the AI wrote it.
        path: Where it is on the card, such as "hazards.0".
        template: The card, with its matrix.
        unreadable: Paths of fields left empty, to add to.

    Returns:
        The hazard as a draft, as written.
    """
    controls: list[ControlDraft] = []
    for index, control in enumerate(written.controls):
        kind: ControlKind | None = None
        if control.kind in {kind.value for kind in ControlKind}:
            kind = ControlKind(control.kind)
        elif control.kind is not None:
            unreadable.append(f"{path}.controls.{index}.kind")
        controls.append(
            ControlDraft(description=control.description.strip(), kind=kind),
        )
    return HazardDraft(
        description=written.description.strip(),
        before=_rating(written.before, f"{path}.before", template, unreadable),
        controls=tuple(controls),
        after=_rating(written.after, f"{path}.after", template, unreadable),
    )


def _rating(
    written: _Rating,
    path: str,
    template: Take5Template,
    unreadable: list[str],
) -> RatingChoice:
    """Keep a rating's likelihood and consequence when the matrix has them.

    Args:
        written: The rating as the AI wrote it.
        path: Where it is on the card, such as "hazards.0.before".
        template: The card, with its matrix.
        unreadable: Paths of fields left empty, to add to.

    Returns:
        The rating, with an unknown level left empty.
    """
    likelihood: str | None = written.likelihood
    consequence: str | None = written.consequence
    if likelihood is not None and likelihood not in template.matrix.likelihoods:
        unreadable.append(f"{path}.likelihood")
        likelihood = None
    if consequence is not None and consequence not in template.matrix.consequences:
        unreadable.append(f"{path}.consequence")
        consequence = None
    return RatingChoice(likelihood=likelihood, consequence=consequence)


def _date_time(written: str | None, unreadable: list[str]) -> datetime | None:
    """Read the card's date and time, when it is a real one.

    Args:
        written: The date and time as the AI wrote it, in ISO 8601, or None.
        unreadable: Paths of fields left empty, to add to.

    Returns:
        The date and time, or None.
    """
    if written is None:
        return None
    try:
        return datetime.fromisoformat(written)
    except ValueError:
        unreadable.append("filled_in_at")
        return None
