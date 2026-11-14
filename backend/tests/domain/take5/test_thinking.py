"""The spec's wording and weak-control examples, independent of HTTP and storage."""

import pytest

from risk_assessment.domain.controls import ControlKind
from risk_assessment.domain.risk import RiskMatrix, rate
from risk_assessment.domain.take5.template import BOOKLET_MATRIX
from risk_assessment.domain.take5.thinking import (
    control_wording_error,
    job_wording_error,
    weak_controls_question,
)

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
