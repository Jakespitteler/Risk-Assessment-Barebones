"""Tests for keeping the AI's reading of a paper card to what the card allows (0033)."""

import json
from datetime import datetime
from typing import Any

from risk_assessment.domain.controls import ControlKind
from risk_assessment.domain.questions import Answer
from risk_assessment.domain.take5.draft import RatingChoice
from risk_assessment.domain.take5.scanned_card import ScannedCard, scanned_card
from risk_assessment.domain.take5.template import BOOKLET_TEMPLATE


def reading(**changes: object) -> str:
    """Write a reply the AI might give for one card, with some fields changed.

    Args:
        **changes: Fields to replace in the reply.

    Returns:
        The reply, as JSON.
    """
    reply: dict[str, Any] = {
        "worker_name": "Sam Example",
        "job": "Change tyre",
        "location": "Workshop bay 2",
        "filled_in_at": "2026-11-18T06:40",
        "answers": {"scope": "Yes", "procedure": "No"},
        "hazards": [
            {
                "description": "Wheel falls",
                "before": {"likelihood": "Possible", "consequence": "Major"},
                "controls": [{"description": "Chock it", "kind": "Wear PPE"}],
                "after": {"likelihood": "Unlikely", "consequence": "Major"},
            },
        ],
        "unreadable": [],
    }
    return json.dumps(reply | changes)


def test_a_whole_card_is_read_as_written_gaps_and_all() -> None:
    """A two-word job and a weak control are kept, not rewritten to pass a rule."""
    card: ScannedCard | None = scanned_card(reading(), BOOKLET_TEMPLATE)

    assert card is not None
    assert card.draft.worker_name == "Sam Example"
    assert card.draft.job == "Change tyre"
    assert card.draft.answers == {"scope": Answer.YES, "procedure": Answer.NO}
    (hazard,) = card.draft.hazards
    assert hazard.before == RatingChoice(likelihood="Possible", consequence="Major")
    assert hazard.controls[0].kind == ControlKind.PPE
    assert card.filled_in_at == datetime(2026, 11, 18, 6, 40)
    assert card.unreadable == ()


def test_a_word_the_card_does_not_have_is_left_empty_and_marked() -> None:
    """An unknown answer, level or kind is never guessed; the person fills it in."""
    hazards: list[dict[str, Any]] = [
        {
            "description": "Wheel falls",
            "before": {"likelihood": "Maybe", "consequence": "Major"},
            "controls": [{"description": "Chock it", "kind": "Good luck"}],
            "after": {"likelihood": "Rare", "consequence": "Huge"},
        },
    ]

    card: ScannedCard | None = scanned_card(
        reading(
            answers={"scope": "Probably", "not_a_question": "Yes"},
            hazards=hazards,
        ),
        BOOKLET_TEMPLATE,
    )

    assert card is not None
    assert card.draft.answers == {}
    (hazard,) = card.draft.hazards
    assert hazard.before.likelihood is None
    assert hazard.controls[0].kind is None
    assert hazard.after.consequence is None
    assert card.unreadable == (
        "answers.scope",
        "hazards.0.controls.0.kind",
        "hazards.0.before.likelihood",
        "hazards.0.after.consequence",
    )


def test_what_the_ai_could_not_read_is_kept_and_a_bad_date_is_marked() -> None:
    """The AI's own list of unreadable fields comes through, with a bad date added."""
    card: ScannedCard | None = scanned_card(
        reading(unreadable=["job"], filled_in_at="Tuesday arvo"),
        BOOKLET_TEMPLATE,
    )

    assert card is not None
    assert card.unreadable == ("job", "filled_in_at")
    assert card.filled_in_at is None


def test_a_reply_in_a_code_fence_is_read() -> None:
    """Models sometimes wrap JSON in a ```json fence."""
    assert scanned_card(f"```json\n{reading()}\n```", BOOKLET_TEMPLATE) is not None


def test_a_reply_that_is_not_the_json_asked_for_is_none() -> None:
    """A refusal, or JSON of the wrong shape, is not a card."""
    assert scanned_card("I can't read this photo.", BOOKLET_TEMPLATE) is None
    assert scanned_card('{"hazards": "lots"}', BOOKLET_TEMPLATE) is None
    assert scanned_card("[1, 2, 3]", BOOKLET_TEMPLATE) is None
