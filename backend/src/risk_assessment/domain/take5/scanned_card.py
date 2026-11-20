"""A paper card as the AI read it, kept to what the template allows (task 0033).

The AI's reply is untrusted. It is read field by field: a field the AI couldn't read
(null), wrote as the wrong kind of value, or wrote with a word the template doesn't have
(an answer, a level or a control kind) is left empty and marked unreadable, for the
person checking the card to fill in from the photo. One bad field never loses the
whole card. Nothing is rewritten to pass a rule: a card is kept as written, gaps and
all.
"""

import json
import re
from datetime import date, datetime
from typing import ClassVar, cast

from pydantic import BaseModel, ConfigDict

from risk_assessment.domain.controls import ControlKind
from risk_assessment.domain.questions import Answer
from risk_assessment.domain.take5.draft import (
    ControlDraft,
    HazardDraft,
    RatingChoice,
    Take5Draft,
)
from risk_assessment.domain.take5.template import Take5Template

# A path the page can put beside a field, such as "job" or "hazards.0.before".
_FIELD_PATH: re.Pattern[str] = re.compile(r"^[a-z_]+(\.[a-z0-9_]+){0,4}$")
_LONGEST_PATH: int = 60
# More hazards or controls than this is not a card.
_MOST_ITEMS: int = 20


class ScannedCard(BaseModel):
    """What the AI read off one paper card, for a person to check.

    Attributes:
        draft: The card as a draft Take 5, with the worker's name as written.
        filled_in_at: The date, or date and time, written on the card, in ISO 8601
            as read (day first on an Australian card), with no time zone: such as
            "2026-04-03" or "2026-04-03T06:40". None when there was none or it
            couldn't be read. The time zone is added when the card is saved.
        unreadable: The paths of the fields left empty for the person to fill in,
            such as "job" or "hazards.0.before.likelihood".
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    draft: Take5Draft
    filled_in_at: str | None = None
    unreadable: tuple[str, ...] = ()


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


def _fields(value: object) -> dict[str, object] | None:
    """Read a JSON object from the AI's reply, with its keys as text.

    Args:
        value: Anything the reply held.

    Returns:
        The object's fields, or None when it wasn't an object.
    """
    if not isinstance(value, dict):
        return None
    return {str(key): item for key, item in cast(dict[object, object], value).items()}


def _items(value: object) -> list[object] | None:
    """Read a JSON list from the AI's reply.

    Args:
        value: Anything the reply held.

    Returns:
        The list's items, or None when it wasn't a list.
    """
    return list(cast(list[object], value)) if isinstance(value, list) else None


class _Reading:
    """Reads one reply field by field, noting each field it has to leave empty."""

    def __init__(self, template: Take5Template, ai_unreadable: object) -> None:
        """Start a reading for this card.

        Args:
            template: The card, with its questions, matrix and kinds.
            ai_unreadable: The AI's own list of paths it couldn't read.
        """
        self.template: Take5Template = template
        self.unreadable: list[str] = [
            path
            for path in _items(ai_unreadable) or []
            if isinstance(path, str)
            and len(path) <= _LONGEST_PATH
            and _FIELD_PATH.match(path)
        ]

    def text(self, value: object, path: str) -> str:
        """Read a piece of writing: absent is blank; null or not text is unreadable.

        Args:
            value: What the AI wrote for the field.
            path: Where the field is on the card.

        Returns:
            The writing, trimmed, or "" when it couldn't be read.
        """
        if isinstance(value, str):
            return value.strip()
        self.unreadable.append(path)
        return ""

    def word(self, value: object, allowed: tuple[str, ...], path: str) -> str | None:
        """Read one of the card's own words, such as a level or a control kind.

        Args:
            value: What the AI wrote.
            allowed: The words the card has for this field.
            path: Where the field is on the card.

        Returns:
            The word, or None when it was missing or not one of the card's.
        """
        if isinstance(value, str) and value in allowed:
            return value
        self.unreadable.append(path)
        return None

    def objects(self, value: object, path: str) -> list[object]:
        """Read a list of things, such as hazards: anything else is unreadable.

        Args:
            value: What the AI wrote.
            path: Where the list is on the card.

        Returns:
            The items, at most `_MOST_ITEMS`.
        """
        items: list[object] | None = _items(value)
        if items is not None:
            return items[:_MOST_ITEMS]
        if value is not None:
            self.unreadable.append(path)
        return []


def scanned_card(reply: str, template: Take5Template) -> ScannedCard | None:
    """Read the AI's reply about one card into a card to check.

    Args:
        reply: The AI's reply: one JSON object, perhaps in a code fence.
        template: The card the photo was of.

    Returns:
        The card, or None when the reply isn't a JSON object at all.
    """
    try:
        loaded: object = json.loads(without_fence(reply))
    except json.JSONDecodeError:
        return None
    card: dict[str, object] | None = _fields(loaded)
    if card is None:
        return None
    reading = _Reading(template, card.get("unreadable"))
    draft = Take5Draft(
        worker_name=reading.text(card.get("worker_name", ""), "worker_name"),
        job=reading.text(card.get("job", ""), "job"),
        location=reading.text(card.get("location", ""), "location"),
        answers=_answers(card.get("answers"), reading),
        hazards=tuple(
            _hazard(hazard, f"hazards.{index}", reading)
            for index, hazard in enumerate(
                reading.objects(card.get("hazards"), "hazards"),
            )
        ),
    )
    return ScannedCard(
        draft=draft,
        filled_in_at=_date_time(card.get("filled_in_at"), reading),
        unreadable=tuple(dict.fromkeys(reading.unreadable)),
    )


def _answers(written: object, reading: _Reading) -> dict[str, Answer]:
    """Keep the answers to the card's own questions that are a real answer.

    Args:
        written: The answers as the AI wrote them, by question id.
        reading: The reading, which notes each answer left empty.

    Returns:
        Each usable answer, by question id.
    """
    answers_written: dict[str, object] | None = _fields(written)
    if answers_written is None:
        return {}
    allowed: tuple[str, ...] = tuple(answer.value for answer in Answer)
    answers: dict[str, Answer] = {}
    for question in reading.template.questions:
        if question.id not in answers_written:
            continue
        word: str | None = reading.word(
            answers_written[question.id],
            allowed,
            f"answers.{question.id}",
        )
        if word is not None:
            answers[question.id] = Answer(word)
    return answers


def _hazard(written: object, path: str, reading: _Reading) -> HazardDraft:
    """Keep one hazard, with only the levels and kinds the template has.

    Args:
        written: The hazard as the AI wrote it.
        path: Where it is on the card, such as "hazards.0".
        reading: The reading, which notes each field left empty.

    Returns:
        The hazard as a draft, as written, or an empty one when it wasn't a hazard.
    """
    hazard: dict[str, object] | None = _fields(written)
    if hazard is None:
        reading.unreadable.append(path)
        return HazardDraft()
    kinds: tuple[str, ...] = tuple(kind.value for kind in ControlKind)
    controls: list[ControlDraft] = []
    for index, control in enumerate(
        reading.objects(hazard.get("controls"), f"{path}.controls"),
    ):
        control_path: str = f"{path}.controls.{index}"
        fields: dict[str, object] | None = _fields(control)
        if fields is None:
            reading.unreadable.append(control_path)
            controls.append(ControlDraft())
            continue
        kind: str | None = reading.word(
            fields.get("kind"),
            kinds,
            f"{control_path}.kind",
        )
        controls.append(
            ControlDraft(
                description=reading.text(
                    fields.get("description", ""),
                    f"{control_path}.description",
                ),
                kind=ControlKind(kind) if kind is not None else None,
            ),
        )
    return HazardDraft(
        description=reading.text(hazard.get("description", ""), f"{path}.description"),
        before=_rating(hazard.get("before"), f"{path}.before", reading),
        controls=tuple(controls),
        after=_rating(hazard.get("after"), f"{path}.after", reading),
    )


def _rating(written: object, path: str, reading: _Reading) -> RatingChoice:
    """Keep a rating's likelihood and consequence when the matrix has them.

    Args:
        written: The rating as the AI wrote it.
        path: Where it is on the card, such as "hazards.0.before".
        reading: The reading, which notes each level left empty.

    Returns:
        The rating, with a missing or unknown level left empty.
    """
    rating: dict[str, object] | None = _fields(written)
    if rating is None:
        reading.unreadable.append(path)
        return RatingChoice()
    return RatingChoice(
        likelihood=reading.word(
            rating.get("likelihood"),
            reading.template.matrix.likelihoods,
            f"{path}.likelihood",
        ),
        consequence=reading.word(
            rating.get("consequence"),
            reading.template.matrix.consequences,
            f"{path}.consequence",
        ),
    )


def _date_time(written: object, reading: _Reading) -> str | None:
    """Keep the card's date, or date and time, when it is a real one.

    A date with no time stays a date, so a card's missing time isn't read as midnight.

    Args:
        written: What the AI wrote, in ISO 8601, or None.
        reading: The reading, which notes a date that couldn't be read.

    Returns:
        The date as written, without a time zone, or None.
    """
    if written is None:
        return None
    if isinstance(written, str):
        text: str = written.strip()
        for parse in (date.fromisoformat, datetime.fromisoformat):
            try:
                parse(text)
            except ValueError:
                continue
            return text
    reading.unreadable.append("filled_in_at")
    return None
