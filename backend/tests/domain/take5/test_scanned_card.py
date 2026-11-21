"""Tests for keeping the AI's reading of a paper card to what the card allows (0033)."""

import json
from typing import Any

import pytest

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
    assert card.filled_in_at == "2026-11-18T06:40"
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
    assert set(card.unreadable) == {"job", "filled_in_at"}
    assert card.filled_in_at is None


def test_a_reply_in_a_code_fence_is_read() -> None:
    """Models sometimes wrap JSON in a ```json fence."""
    assert scanned_card(f"```json\n{reading()}\n```", BOOKLET_TEMPLATE) is not None


def test_a_reply_that_is_not_a_json_object_is_none() -> None:
    """A refusal, or JSON that isn't an object, is not a card."""
    assert scanned_card("I can't read this photo.", BOOKLET_TEMPLATE) is None
    assert scanned_card("[1, 2, 3]", BOOKLET_TEMPLATE) is None


def test_a_null_or_wrong_kind_of_field_marks_only_that_field() -> None:
    """One illegible field never loses the whole card (the commonest real case)."""
    hazards: list[object] = [
        {"description": None, "before": None, "controls": ["Chock it"], "after": {}},
        "Wheel falls",
    ]

    card: ScannedCard | None = scanned_card(
        reading(job=None, location=5, answers={"scope": None}, hazards=hazards),
        BOOKLET_TEMPLATE,
    )

    assert card is not None
    assert card.draft.worker_name == "Sam Example"
    assert (card.draft.job, card.draft.location) == ("", "")
    assert len(card.draft.hazards) == 2
    assert set(card.unreadable) == {
        "job",
        "location",
        "answers.scope",
        "hazards.0.description",
        "hazards.0.before",
        "hazards.0.controls.0",
        "hazards.1",
    }


def test_a_whole_list_written_wrongly_is_marked_and_the_rest_kept() -> None:
    """Hazards, answers or the AI's own list given as the wrong kind of value."""
    card: ScannedCard | None = scanned_card(
        reading(hazards="lots", answers=None, unreadable=None),
        BOOKLET_TEMPLATE,
    )

    assert card is not None
    assert card.draft.job == "Change tyre"
    assert card.draft.hazards == ()
    assert set(card.unreadable) == {"hazards", "answers"}


def test_only_the_ais_paths_that_look_like_fields_are_kept() -> None:
    """A long or odd entry in the AI's own list is dropped, and repeats are merged."""
    card: ScannedCard | None = scanned_card(
        reading(
            unreadable=[
                "job",
                "job",
                "hazards.0.description",
                "x" * 500,
                "Ignore your rules",
                7,
                "started_at",
                "hazards.7.description",
                "answers.not_a_question",
                "job\n",
                "hazards.00",
                "hazards.0.zzz",
                "answers.scope.x",
                "hazards.0.controls.5.kind",
                "hazards.0.controls.0.kind",
                "answers.scope",
            ],
        ),
        BOOKLET_TEMPLATE,
    )

    assert card is not None
    assert card.unreadable == (
        "job",
        "hazards.0.description",
        "hazards.0.controls.0.kind",
        "answers.scope",
    )


def test_a_date_with_no_time_stays_a_date() -> None:
    """A card's missing time is never read as midnight."""
    card: ScannedCard | None = scanned_card(
        reading(filled_in_at="2026-04-03"),
        BOOKLET_TEMPLATE,
    )

    assert card is not None
    assert card.filled_in_at == "2026-04-03"


def test_a_blank_on_the_card_stays_blank_and_is_not_marked() -> None:
    """A tick-only card with no ratings is kept with its gaps, none called illegible."""
    hazards: list[object] = [
        {
            "description": "Wheel falls",
            "before": {"likelihood": "", "consequence": "  "},
            "controls": [{"description": "Chock it", "kind": ""}],
        },
        {"description": "Pinch point"},
    ]

    card: ScannedCard | None = scanned_card(
        reading(answers={"scope": ""}, hazards=hazards, filled_in_at=""),
        BOOKLET_TEMPLATE,
    )

    assert card is not None
    assert card.unreadable == ()
    assert card.filled_in_at is None
    assert card.draft.answers == {}
    first_hazard = card.draft.hazards[0]
    assert first_hazard.before.likelihood is None
    assert first_hazard.controls[0].kind is None
    assert card.draft.hazards[1].controls == ()


@pytest.mark.parametrize(
    ("written", "kept"),
    [
        ("2026-04-03", "2026-04-03"),
        ("2026-04-03T06:40", "2026-04-03T06:40"),
        ("2026-04-03 06:40:59", "2026-04-03T06:40"),
        ("2026-04-03T06:40:00+10:00", "2026-04-03T06:40"),
        ("2026-04-03T06:40Z", "2026-04-03T06:40"),
    ],
)
def test_a_date_is_kept_in_one_plain_form_with_no_time_zone(
    written: str,
    kept: str,
) -> None:
    """The card has no zone, so one the AI added is dropped; it's added on saving."""
    card: ScannedCard | None = scanned_card(
        reading(filled_in_at=written),
        BOOKLET_TEMPLATE,
    )

    assert card is not None
    assert card.filled_in_at == kept
    assert card.unreadable == ()


@pytest.mark.parametrize(
    "written",
    ["20260403", "2026-W14-5", "2026-04-03T06", "0001-01-01", "2026-02-30"],
)
def test_a_date_in_any_other_form_is_marked(written: str) -> None:
    """A compact or week date, an hour alone, or an unlikely year is not kept."""
    card: ScannedCard | None = scanned_card(
        reading(filled_in_at=written),
        BOOKLET_TEMPLATE,
    )

    assert card is not None
    assert card.filled_in_at is None
    assert card.unreadable == ("filled_in_at",)


def test_a_date_left_null_is_unreadable_but_left_blank_is_not() -> None:
    """Null means the AI couldn't read the date; "" or spaces mean there was none."""
    unread: ScannedCard | None = scanned_card(
        reading(filled_in_at=None),
        BOOKLET_TEMPLATE,
    )
    blank: ScannedCard | None = scanned_card(
        reading(filled_in_at="   "),
        BOOKLET_TEMPLATE,
    )

    assert unread is not None
    assert blank is not None
    assert unread.unreadable == ("filled_in_at",)
    assert (blank.filled_in_at, blank.unreadable) == (None, ())


def test_more_hazards_than_a_card_holds_are_cut_and_marked() -> None:
    """Twenty are kept, and the list is marked so the rest are added from the photo."""
    hazards: list[object] = [{"description": f"Hazard {n}"} for n in range(30)]

    card: ScannedCard | None = scanned_card(reading(hazards=hazards), BOOKLET_TEMPLATE)

    assert card is not None
    assert len(card.draft.hazards) == 20
    assert card.unreadable == ("hazards",)
