"""Tests for saving a checked paper card as written (spec P1 to P5, task 0033)."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest

from risk_assessment.domain.controls import ControlKind
from risk_assessment.domain.questions import Answer
from risk_assessment.domain.risk import RiskRating
from risk_assessment.domain.take5.areas import risk_by_area
from risk_assessment.domain.take5.draft import (
    ControlDraft,
    HazardDraft,
    RatingChoice,
    Take5Draft,
)
from risk_assessment.domain.take5.paper import (
    PaperCardError,
    paper_started_at,
    saved_paper_take5,
)
from risk_assessment.domain.take5.ranking import (
    highest_score,
    is_careful,
    minutes_taken,
    rank_by_rules,
    ranking_text,
    rule_line,
    thought_gaps,
    typical_minutes,
    worst_score,
)
from risk_assessment.domain.take5.saved import SavedTake5
from risk_assessment.domain.take5.template import BOOKLET_TEMPLATE
from risk_assessment.domain.take5.verdict import NO_HAZARD_REASON
from tests.samples import sample_answers

PERTH: str = "Australia/Perth"
SCANNED_AT: datetime = datetime(2026, 11, 21, 2, 0, tzinfo=UTC)
WHEEL: str = "The wheel falls off the hub onto a foot"
POSSIBLE_MAJOR = RatingChoice(likelihood="Possible", consequence="Major")


def paper_card(
    *hazards: HazardDraft,
    answers: dict[str, Answer] | None = None,
    job: str = "Change the front tyre on LV12",
    filled_in_at: str | None = "2026-11-21",
    time_zone: str = PERTH,
) -> SavedTake5:
    """Save a checked paper card, as the scan page sends it.

    Args:
        *hazards: The card's hazards, as checked.
        answers: The answers; every question answered when left out.
        job: The job, as written.
        filled_in_at: The card's date, as read and checked.
        time_zone: The checker's time zone.

    Returns:
        The saved paper Take 5.
    """
    draft = Take5Draft(
        worker_name="Sam Example",
        job=job,
        location="Workshop bay 2",
        answers=answers if answers is not None else sample_answers(),
        hazards=hazards,
    )
    return saved_paper_take5(
        uuid4(),
        draft,
        filled_in_at,
        time_zone,
        BOOKLET_TEMPLATE,
        SCANNED_AT,
    )


def test_example_131_a_card_with_ticks_only_is_saved_and_told_not_to_start() -> None:
    """No hazard is saved as written: a reason and a gap, never a form error (P1)."""
    card: SavedTake5 = paper_card()

    assert card.from_paper
    assert card.hazards == ()
    assert card.is_finished
    assert card.challenge is None
    assert card.verdict is not None
    assert not card.verdict.can_start
    assert card.verdict.reasons == (NO_HAZARD_REASON,)
    assert "no hazard was written down" in thought_gaps(card)


def test_example_132_a_hazard_with_no_after_rating_counts_at_its_before() -> None:
    """A card rated before controls only isn't read as safer than it said (P2)."""
    card: SavedTake5 = paper_card(HazardDraft(description=WHEEL, before=POSSIBLE_MAJOR))

    assert card.hazards[0].after is None
    rating: RiskRating | None = card.rating
    assert rating is not None
    assert (rating.score, rating.band) == (18, "Extreme")
    assert card.verdict is not None
    assert card.verdict.reasons[0] == f"Say how you will control: {WHEEL}"
    assert card.verdict.reasons[1].startswith("The risk is Extreme (18).")


def test_example_133_no_rating_and_no_kind_are_a_reason_and_gaps() -> None:
    """Blanks are kept blank: a reason (P3) and gaps counted against it (P4)."""
    card: SavedTake5 = paper_card(
        HazardDraft(
            description=WHEEL,
            controls=(ControlDraft(description="Chock it"),),
        ),
    )

    assert card.hazards[0].before is None
    assert card.hazards[0].controls[0].kind is None
    assert card.rating is None
    assert card.verdict is not None
    assert card.verdict.reasons == (f"Rate the risk of: {WHEEL}",)
    assert thought_gaps(card) == (
        f"“{WHEEL}” has no rating",
        f"a control for “{WHEEL}” has no kind",
    )
    assert highest_score(card) == 0
    assert worst_score(card) == 10
    assert rule_line(card).startswith("No risk rated. ")


def test_example_134_a_blank_answer_is_a_gap_but_never_a_reason() -> None:
    """A question left blank isn't read as No."""
    answers: dict[str, Answer] = sample_answers()
    del answers["scope"]

    card: SavedTake5 = paper_card(
        HazardDraft(
            description=WHEEL,
            before=POSSIBLE_MAJOR,
            controls=(ControlDraft(description="Chock it", kind=ControlKind.PPE),),
            after=RatingChoice(likelihood="Unlikely", consequence="Minor"),
        ),
        answers=answers,
    )

    assert "scope" not in card.answers
    assert card.verdict is not None
    assert card.verdict.can_start
    assert thought_gaps(card)[0].endswith("has no answer")


def test_example_135_controls_that_raise_the_risk_are_kept_as_written() -> None:
    """R6 doesn't apply: the card says what it says."""
    card: SavedTake5 = paper_card(
        HazardDraft(
            description=WHEEL,
            before=RatingChoice(likelihood="Unlikely", consequence="Minor"),
            controls=(ControlDraft(description="Chock it", kind=ControlKind.PPE),),
            after=RatingChoice(likelihood="Possible", consequence="Minor"),
        ),
    )

    assert card.rating is not None
    assert card.rating.score == 8


def test_example_136_short_words_are_kept_with_no_form_error() -> None:
    """T2 and T4 don't apply to a paper card."""
    card: SavedTake5 = paper_card(
        HazardDraft(
            description=WHEEL,
            before=POSSIBLE_MAJOR,
            controls=(ControlDraft(description="Be careful", kind=ControlKind.PPE),),
            after=POSSIBLE_MAJOR,
        ),
        job="Tyre",
    )

    assert card.job == "Tyre"
    assert card.hazards[0].controls[0].description == "Be careful"


def test_example_137_a_date_alone_is_the_start_of_that_day_where_the_checker_is() -> (
    None
):
    """Midnight in Perth, at +08:00 (P5)."""
    started_at: datetime | None = paper_started_at("2026-04-03", PERTH)

    assert started_at == datetime(2026, 4, 3, tzinfo=ZoneInfo(PERTH))
    assert started_at is not None
    assert started_at.utcoffset() == timedelta(hours=8)


def test_example_138_a_date_and_time_take_the_checkers_zone_with_daylight_saving() -> (
    None
):
    """Sydney is at +11:00 in April 2026 until daylight saving ends on the 5th."""
    started_at: datetime | None = paper_started_at(
        "2026-04-03T06:40",
        "Australia/Sydney",
    )

    assert started_at is not None
    assert (started_at.hour, started_at.minute) == (6, 40)
    assert started_at.utcoffset() == timedelta(hours=11)


def test_example_139_no_date_leaves_the_start_empty_for_the_scan_time() -> None:
    """The ranking then goes by when it was saved."""
    card: SavedTake5 = paper_card(filled_in_at=None)

    assert card.started_at is None
    assert card.created_at == SCANNED_AT


def test_example_140_a_paper_cards_time_taken_is_never_known() -> None:
    """Never rushed, never timed, never the best."""
    card: SavedTake5 = paper_card(
        HazardDraft(
            description=WHEEL,
            before=POSSIBLE_MAJOR,
            controls=(
                ControlDraft(
                    description="Chock both wheels",
                    kind=ControlKind.BARRICADE,
                ),
            ),
            after=RatingChoice(likelihood="Unlikely", consequence="Minor"),
        ),
        filled_in_at="2026-11-21T09:50",
    )

    assert card.started_at is not None
    assert SCANNED_AT - card.started_at == timedelta(minutes=10)
    assert minutes_taken(card) is None
    assert typical_minutes([card]) is None
    assert not any("under 2 minutes" in gap for gap in thought_gaps(card))
    assert not is_careful(card)


@pytest.mark.parametrize(
    ("filled_in_at", "time_zone", "path"),
    [
        ("03/04/2026", PERTH, "filled_in_at"),
        ("2026-02-30", PERTH, "filled_in_at"),
        ("2026-04-03", "Mars/Olympus", "time_zone"),
    ],
)
def test_a_date_or_zone_that_cant_be_read_is_refused_by_its_field(
    filled_in_at: str,
    time_zone: str,
    path: str,
) -> None:
    """The page sends the date as the card was read; anything else is a mistake."""
    with pytest.raises(PaperCardError) as raised:
        paper_started_at(filled_in_at, time_zone)

    assert raised.value.path == path


def test_a_level_not_on_the_card_is_refused_by_its_field() -> None:
    """Only what no card can hold is refused."""
    with pytest.raises(PaperCardError) as raised:
        paper_card(
            HazardDraft(
                description=WHEEL,
                before=RatingChoice(likelihood="Sometimes", consequence="Major"),
            ),
        )

    assert raised.value.path == "hazards.0.before.likelihood"


def test_a_rating_with_one_half_is_kept_blank() -> None:
    """It can't be scored, so it counts as no rating."""
    card: SavedTake5 = paper_card(
        HazardDraft(description=WHEEL, before=RatingChoice(likelihood="Possible")),
    )

    assert card.hazards[0].before is None


def test_the_name_read_off_a_card_never_goes_to_the_ranking_ai() -> None:
    """The name fills in the card, and stays out of every other AI call (P6)."""
    card: SavedTake5 = paper_card(
        HazardDraft(
            description=WHEEL,
            controls=(ControlDraft(description="Chock it"),),
        ),
    )

    text: str = ranking_text(rank_by_rules([card]))

    assert card.worker_name == "Sam Example"
    assert "Sam Example" not in text
    assert "not rated" in text
    assert "not given" in text


def test_an_area_of_unrated_paper_cards_has_no_highest_risk() -> None:
    """Risk by area says nothing rated rather than a made-up score (P4, A5)."""
    card: SavedTake5 = paper_card(HazardDraft(description=WHEEL))

    (area,) = risk_by_area([card])

    assert (area.highest_score, area.highest_band) == (None, None)
    assert area.high_risk_count == 0
    assert area.thought_gap_count == 1
