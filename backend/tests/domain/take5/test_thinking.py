"""The spec's thinking-rule examples (T2 to T6), independent of HTTP and storage."""

import pytest

from risk_assessment.domain.controls import ControlKind
from risk_assessment.domain.questions import Answer
from risk_assessment.domain.risk import RiskMatrix, rate
from risk_assessment.domain.take5.template import BOOKLET_MATRIX, BOOKLET_TEMPLATE
from risk_assessment.domain.take5.thinking import (
    control_wording_error,
    hazard_wording_nudge,
    job_wording_error,
    unlinked_yes_answers,
    weak_controls_question,
)
from tests.samples import sample_answers

QUESTION: str = (
    "Everything here relies on people getting it right. "
    "Could you remove, isolate or barricade it?"
)


def test_example_28_a_vague_control_is_refused() -> None:
    """Case and a final full stop do not turn a vague phrase into a control."""
    assert control_wording_error("Be careful.") == "Say what you'll actually do."


def test_example_29_a_longer_control_is_accepted() -> None:
    """An exact phrase is refused, not every sentence containing it."""
    assert (
        control_wording_error("Be careful of the pinch point when lowering the tray")
        is None
    )


def test_example_30_a_serious_hazard_with_only_weak_controls_is_asked() -> None:
    """PPE and behaviour both rely on the worker getting it right."""
    assert (
        weak_controls_question(
            rate(BOOKLET_MATRIX, "Possible", "Major"),
            (ControlKind.PPE, ControlKind.BEHAVIOUR),
            BOOKLET_MATRIX,
        )
        == QUESTION
    )


@pytest.mark.parametrize(
    "strong",
    [ControlKind.REMOVE, ControlKind.ISOLATE, ControlKind.BARRICADE],
)
def test_example_31_one_strong_control_means_no_question(strong: ControlKind) -> None:
    """Isolation, and either of the other strong kinds, is enough."""
    assert (
        weak_controls_question(
            rate(BOOKLET_MATRIX, "Possible", "Major"),
            (ControlKind.PPE, strong),
            BOOKLET_MATRIX,
        )
        is None
    )


def test_example_32_below_the_threshold_is_not_asked() -> None:
    """A before score of 10 does not trigger T3."""
    assert (
        weak_controls_question(
            rate(BOOKLET_MATRIX, "Rare", "Major"),
            (ControlKind.PPE,),
            BOOKLET_MATRIX,
        )
        is None
    )


def test_example_33_exactly_the_threshold_is_asked() -> None:
    """A before score of 11 with systems alone triggers T3."""
    assert (
        weak_controls_question(
            rate(BOOKLET_MATRIX, "Almost Certain", "Low"),
            (ControlKind.SYSTEMS,),
            BOOKLET_MATRIX,
        )
        == QUESTION
    )


def test_example_34_no_controls_means_no_question() -> None:
    """V2 covers a hazard without controls; T3 does not ask about it."""
    assert (
        weak_controls_question(
            rate(BOOKLET_MATRIX, "Possible", "Major"),
            (),
            BOOKLET_MATRIX,
        )
        is None
    )


def test_example_37_two_words_are_not_a_job_description() -> None:
    """The error explains the four-word minimum."""
    assert (
        job_wording_error("Change tyre") == "Describe the job in at least four words."
    )


def test_example_38_three_words_are_still_too_short() -> None:
    """One word below the boundary fails."""
    assert (
        job_wording_error("Change the tyre")
        == "Describe the job in at least four words."
    )


def test_example_39_exactly_four_words_are_accepted() -> None:
    """An equipment identifier counts as a word."""
    assert job_wording_error("Change tyre on LV12") is None


def test_the_threshold_comes_from_the_given_matrix() -> None:
    """Another card can ask at a different score without changing the rule."""
    matrix: RiskMatrix = BOOKLET_MATRIX.model_copy(update={"jha_threshold": 8})
    assert (
        weak_controls_question(
            rate(matrix, "Possible", "Minor"),
            (ControlKind.PPE,),
            matrix,
        )
        == QUESTION
    )


def test_example_65_a_yes_with_no_hazard_linked_is_named() -> None:
    """T5: the heights question answered Yes needs a hazard on the list."""
    assert unlinked_yes_answers(
        BOOKLET_TEMPLATE.questions,
        sample_answers(heights=Answer.YES),
        (),
    ) == ("heights",)


def test_example_67_one_hazard_can_cover_two_questions() -> None:
    """T5: one hazard linked to both the vehicles and hazardous materials questions."""
    assert (
        unlinked_yes_answers(
            BOOKLET_TEMPLATE.questions,
            sample_answers(vehicles=Answer.YES, hazardous_materials=Answer.YES),
            ("vehicles", "hazardous_materials"),
        )
        == ()
    )


@pytest.mark.parametrize("answer", [Answer.NO, Answer.NOT_APPLICABLE])
def test_example_68_a_no_or_na_needs_no_hazard(answer: Answer) -> None:
    """T5 only asks about a Yes."""
    assert (
        unlinked_yes_answers(
            BOOKLET_TEMPLATE.questions,
            sample_answers(heights=answer),
            (),
        )
        == ()
    )


def test_a_no_to_a_stop_question_never_needs_a_hazard() -> None:
    """T5 is about hazard questions; a stop question's No is V1's business."""
    assert (
        unlinked_yes_answers(
            BOOKLET_TEMPLATE.questions,
            sample_answers(permits=Answer.NO),
            (),
        )
        == ()
    )


VEHICLES_NUDGE: str = (
    "Make it specific: say what could hurt you, and where. "
    'For example: "Hit by a haul truck at the crib hut crossing"'
)
VEHICLES_EXAMPLE: str = "Hit by a haul truck at the crib hut crossing"


def test_example_70_a_five_word_hazard_is_nudged_with_the_example() -> None:
    """T6: "Get hit by a car" is one word short of six."""
    assert (
        hazard_wording_nudge("Get hit by a car", VEHICLES_EXAMPLE, 6) == VEHICLES_NUDGE
    )


def test_example_71_a_six_word_hazard_is_not_nudged() -> None:
    """T6: exactly six words is enough."""
    assert (
        hazard_wording_nudge("Hit by a truck reversing nearby", VEHICLES_EXAMPLE, 6)
        is None
    )


def test_example_72_a_specific_hazard_is_not_nudged() -> None:
    """T6: what could hurt, and where, in ten words."""
    assert hazard_wording_nudge(VEHICLES_EXAMPLE, VEHICLES_EXAMPLE, 6) is None


def test_example_74_a_card_with_no_word_minimum_never_nudges() -> None:
    """T6: a template whose minimum is None turns the nudge off."""
    assert hazard_wording_nudge("Car", VEHICLES_EXAMPLE, None) is None


def test_a_question_with_no_example_nudges_without_one() -> None:
    """A card that gives no example still gets the nudge, just without one."""
    assert (
        hazard_wording_nudge("Car", "", 6)
        == "Make it specific: say what could hurt you, and where."
    )


def test_a_blank_hazard_is_left_to_the_fill_in_error() -> None:
    """A blank hazard already has its own error, so it isn't nudged as well."""
    assert hazard_wording_nudge("   ", VEHICLES_EXAMPLE, 6) is None
