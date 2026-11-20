"""Tests for risk by area (spec A1 to A5), from the worked examples."""

from datetime import UTC, datetime, timedelta

from risk_assessment.domain.questions import Answer
from risk_assessment.domain.risk import rate
from risk_assessment.domain.take5.areas import (
    AreaRisk,
    CommonYes,
    area_key,
    area_since,
    is_high_risk,
    risk_by_area,
)
from risk_assessment.domain.take5.saved import SavedTake5
from risk_assessment.domain.take5.take5 import Hazard
from risk_assessment.domain.take5.template import BOOKLET_MATRIX
from risk_assessment.domain.take5.verdict import Verdict
from tests.domain.take5.test_ranking import SAVED_AT, ranked_take5
from tests.samples import BARRICADE, sample_answers

WORKSHOP: str = "Light vehicle workshop"
DONT_START: Verdict = Verdict(can_start=False, reasons=("You don't have a permit.",))


def area_take5(
    location: str = WORKSHOP,
    before: tuple[str, str] = ("Possible", "Minor"),
    minutes_before: float = 0,
    **yes: Answer,
) -> SavedTake5:
    """Make the ranking examples' careful Take 5 in an area.

    Args:
        location: Where the job is, as typed.
        before: The hazard's likelihood and consequence before a barricade, which
            leaves it Rare / Low.
        minutes_before: How many minutes before the others it was saved.
        **yes: Hazard questions answered Yes, such as `vehicles=Answer.YES`.

    Returns:
        The saved Take 5, with no thought gaps.
    """
    take5: SavedTake5 = ranked_take5(
        saved_at=SAVED_AT - timedelta(minutes=minutes_before),
    )
    return take5.model_copy(
        update={
            "location": location,
            "answers": sample_answers(**yes),
            "hazards": (
                Hazard(
                    description=take5.hazards[0].description,
                    before=rate(BOOKLET_MATRIX, *before),
                    controls=(BARRICADE,),
                    after=rate(BOOKLET_MATRIX, "Rare", "Low"),
                ),
            ),
        },
    )


def test_example_119_spellings_of_one_place_are_one_area() -> None:
    """A1: capitals, spaces and punctuation are ignored; the most typed name shows."""
    areas: tuple[AreaRisk, ...] = risk_by_area(
        (
            area_take5(WORKSHOP),
            area_take5("light-vehicle  workshop.", minutes_before=1),
            area_take5(WORKSHOP, minutes_before=2),
        ),
    )

    assert [(area.name, area.take5_count) for area in areas] == [(WORKSHOP, 3)]


def test_example_120_on_a_tie_the_newest_spelling_shows() -> None:
    """A1: each spelling typed once, so the newest Take 5's spelling names the area."""
    areas: tuple[AreaRisk, ...] = risk_by_area(
        (
            area_take5("LV workshop", minutes_before=5),
            area_take5("lv  WORKSHOP"),
        ),
    )

    assert areas[0].name == "lv  WORKSHOP"


def test_example_121_a_take5_with_no_location_is_left_out() -> None:
    """A1: punctuation alone isn't a place, so it can't be placed."""
    assert risk_by_area((area_take5(" - "),)) == ()


def test_example_122_a_hazard_needing_a_jha_is_high_risk() -> None:
    """A3: Almost Certain / Low is 11, which needs a JHA on the booklet (R3)."""
    assert is_high_risk(area_take5(before=("Almost Certain", "Low")))


def test_example_123_a_hazard_under_the_jha_threshold_is_not() -> None:
    """A3: Rare / Major is 10, one under the booklet's JHA threshold."""
    assert not is_high_risk(area_take5(before=("Rare", "Major")))


def test_example_124_more_high_risk_take5s_come_first() -> None:
    """A4: one high-risk Take 5 beats three that aren't."""
    areas: tuple[AreaRisk, ...] = risk_by_area(
        (
            area_take5("Crusher", before=("Possible", "Major")),
            area_take5(WORKSHOP),
            area_take5(WORKSHOP),
            area_take5(WORKSHOP),
        ),
    )

    assert [area.name for area in areas] == ["Crusher", WORKSHOP]
    assert (areas[0].high_risk_count, areas[0].highest_score) == (1, 18)
    assert areas[0].highest_band == "Extreme"


def test_example_125_then_more_dont_start_yet_comes_first() -> None:
    """A4: equal high-risk counts, so the area with a "Don't start yet" is hotter."""
    stopped: SavedTake5 = area_take5("Crusher").model_copy(
        update={"verdict": DONT_START},
    )

    areas: tuple[AreaRisk, ...] = risk_by_area((area_take5(WORKSHOP), stopped))

    assert [(area.name, area.dont_start_count) for area in areas] == [
        ("Crusher", 1),
        (WORKSHOP, 0),
    ]


def test_example_126_then_more_thought_gaps_come_first() -> None:
    """A4: all else equal, the area whose answers show less thought is hotter."""
    unanswered: SavedTake5 = ranked_take5(answer=None).model_copy(
        update={"location": "Crusher"},
    )

    areas: tuple[AreaRisk, ...] = risk_by_area((area_take5(WORKSHOP), unanswered))

    assert [(area.name, area.thought_gap_count) for area in areas] == [
        ("Crusher", 1),
        (WORKSHOP, 0),
    ]


def test_example_127_the_most_common_yes_answers_show() -> None:
    """A5: up to 3, the most often first, in the card's order on a tie."""
    areas: tuple[AreaRisk, ...] = risk_by_area(
        (
            area_take5(vehicles=Answer.YES, other=Answer.YES),
            area_take5(vehicles=Answer.YES, heights=Answer.YES),
            area_take5(vehicles=Answer.YES, guards=Answer.YES),
        ),
    )

    assert areas[0].common_yes == (
        CommonYes(
            question=(
                "Am I or others at risk from the operation of vehicles or mobile "
                "equipment?"
            ),
            count=3,
        ),
        CommonYes(
            question="Will I be operating equipment with the guards removed?",
            count=1,
        ),
        CommonYes(question="Will I be working at heights?", count=1),
    )


def test_example_128_the_last_30_days_start_29_midnights_ago() -> None:
    """A2: today counts as one of the 30 days."""
    midnight: datetime = datetime(2026, 11, 21, tzinfo=UTC)

    assert area_since(midnight) == datetime(2026, 10, 23, tzinfo=UTC)


def test_example_130_an_unfinished_take5_has_no_dont_start_yet() -> None:
    """A4: an unfinished Take 5 has no verdict yet, but can still be high risk."""
    unfinished: SavedTake5 = ranked_take5(
        before=("Possible", "Major"),
        answer=None,
    ).model_copy(update={"location": WORKSHOP})

    area: AreaRisk = risk_by_area((unfinished,))[0]

    assert (area.high_risk_count, area.dont_start_count) == (1, 0)


def test_the_area_key_keeps_only_words() -> None:
    """A1: the key is the place's words in lower case, one space apart."""
    assert area_key("  Pit 2, bench-7  ") == "pit 2 bench 7"
