"""Worked examples 18 to 27: the verdict rules V1 to V3, word for word."""

from collections.abc import Mapping

import pytest

from risk_assessment.domain.controls import Control
from risk_assessment.domain.questions import Answer, Question, QuestionRole
from risk_assessment.domain.risk import rate
from risk_assessment.domain.take5.take5 import Hazard, Take5
from risk_assessment.domain.take5.template import (
    BOOKLET_MATRIX,
    BOOKLET_TEMPLATE,
    Take5Template,
)
from risk_assessment.domain.take5.verdict import Verdict, verdict
from tests.samples import BARRICADE, sample_answers, sample_hazard


def _take5(
    before: tuple[str, str] = ("Possible", "Minor"),
    after: tuple[str, str] = ("Unlikely", "Minor"),
    controls: tuple[Control, ...] = (BARRICADE,),
    answers: Mapping[str, Answer] | None = None,
) -> Take5:
    """Make the spec's default Take 5 for these examples: 8 then 5, with a barricade.

    Args:
        before: The likelihood and consequence before controls.
        after: The likelihood and consequence after controls. Ignored with no controls.
        controls: The controls.
        answers: The answers. With none, every think-through question is Yes and
            every hazard question is No.

    Returns:
        The rated Take 5.
    """
    return Take5(
        template=BOOKLET_TEMPLATE,
        answers=sample_answers() if answers is None else answers,
        hazards=(sample_hazard(before, after if controls else before, controls),),
    )


def test_example_18_nothing_different_is_good_to_go() -> None:
    """No reason applies, so the job can start."""
    assert verdict(_take5()) == Verdict(can_start=True, reasons=())


PERMITS_REASON: str = (
    "You answered No to: Do you have the necessary permits? Sort this out first."
)
PPE_REASON: str = (
    "You answered No to: Do you have the correct PPE? Sort this out first."
)
JHA_REASON_AT_12: str = (
    "The risk is High (12). At 11 or more you need a JHA before you start. "
    "Talk to your supervisor."
)


def test_example_19_a_no_to_a_think_through_question_stops_the_job() -> None:
    """V1 names the question answered No."""
    result: Verdict = verdict(_take5(answers=sample_answers(permits=Answer.NO)))

    assert result == Verdict(can_start=False, reasons=(PERMITS_REASON,))


def test_example_20_na_to_a_think_through_question_is_good_to_go() -> None:
    """N/A never stops a job."""
    result: Verdict = verdict(
        _take5(answers=sample_answers(permits=Answer.NOT_APPLICABLE)),
    )

    assert result == Verdict(can_start=True, reasons=())


def test_example_21_yes_to_a_hazard_question_is_good_to_go() -> None:
    """A hazard question is a prompt to list the hazard, not a verdict rule.

    The hazard is linked to the Yes, as T5 needs before it can be submitted.
    """
    take5: Take5 = _take5(answers=sample_answers(heights=Answer.YES))
    linked: Take5 = take5.model_copy(
        update={
            "hazards": (take5.hazards[0].model_copy(update={"covers": ("heights",)}),),
        },
    )

    result: Verdict = verdict(linked)

    assert result == Verdict(can_start=True, reasons=())


def test_example_26_a_no_comes_before_a_hazard_with_no_controls() -> None:
    """Every reason is shown, V1 then V2."""
    result: Verdict = verdict(
        _take5(controls=(), answers=sample_answers(ppe=Answer.NO)),
    )

    assert result == Verdict(
        can_start=False,
        reasons=(PPE_REASON, "Say how you will control: Moving wheel"),
    )


def test_example_27_a_no_comes_before_the_jha_reason() -> None:
    """Every reason is shown, V1 then V3."""
    result: Verdict = verdict(
        _take5(
            before=("Likely", "Minor"),
            after=("Likely", "Minor"),
            answers=sample_answers(ppe=Answer.NO),
        ),
    )

    assert result == Verdict(can_start=False, reasons=(PPE_REASON, JHA_REASON_AT_12))


def test_each_no_is_its_own_reason_in_the_order_of_the_card() -> None:
    """Two questions answered No give two reasons, PPE before permits as printed."""
    result: Verdict = verdict(
        _take5(answers=sample_answers(permits=Answer.NO, ppe=Answer.NO)),
    )

    assert result.reasons == (PPE_REASON, PERMITS_REASON)


# A made-up card whose two questions have the same wording but different roles, so a
# test can prove that V1 reads the role and never the words.
_SAME_WORDS: str = "Is the gate shut?"
_MADE_UP_TEMPLATE = Take5Template(
    name="Example card",
    questions=(
        Question(id="gate_stop", text=_SAME_WORDS, role=QuestionRole.STOP),
        Question(id="gate_hazard", text=_SAME_WORDS, role=QuestionRole.HAZARD),
    ),
    matrix=BOOKLET_MATRIX,
)


@pytest.mark.parametrize(
    ("answers", "expected_reasons"),
    [
        (
            {"gate_stop": Answer.NO, "gate_hazard": Answer.YES},
            ("You answered No to: Is the gate shut? Sort this out first.",),
        ),
        ({"gate_stop": Answer.YES, "gate_hazard": Answer.NO}, ()),
        ({"gate_stop": Answer.NOT_APPLICABLE, "gate_hazard": Answer.NO}, ()),
    ],
)
def test_v1_works_from_the_questions_role_not_its_wording(
    answers: dict[str, Answer],
    expected_reasons: tuple[str, ...],
) -> None:
    """Only a No to a stop question stops the job, whatever the card's wording."""
    take5 = Take5(
        template=_MADE_UP_TEMPLATE,
        answers=answers,
        hazards=(sample_hazard(),),
    )

    assert verdict(take5).reasons == expected_reasons


def test_example_22_a_hazard_with_no_controls_says_how_to_control_it() -> None:
    """V2 names the hazard that has no controls."""
    assert verdict(_take5(controls=())) == Verdict(
        can_start=False,
        reasons=("Say how you will control: Moving wheel",),
    )


def test_example_23_a_rating_of_12_needs_a_jha() -> None:
    """V3 applies at 11 or more."""
    result: Verdict = verdict(
        _take5(before=("Likely", "Minor"), after=("Likely", "Minor")),
    )

    assert result == Verdict(
        can_start=False,
        reasons=(
            "The risk is High (12). At 11 or more you need a JHA before you start. "
            "Talk to your supervisor.",
        ),
    )


def test_example_24_a_rating_of_exactly_11_needs_a_jha() -> None:
    """V3 applies at exactly the threshold."""
    result: Verdict = verdict(
        _take5(before=("Almost Certain", "Low"), after=("Almost Certain", "Low")),
    )

    assert result == Verdict(
        can_start=False,
        reasons=(
            "The risk is High (11). At 11 or more you need a JHA before you start. "
            "Talk to your supervisor.",
        ),
    )


def test_example_25_an_after_rating_of_10_is_good_to_go() -> None:
    """V3 uses the after rating, and 10 is below the threshold."""
    result: Verdict = verdict(
        _take5(before=("Possible", "Major"), after=("Rare", "Major")),
    )

    assert result == Verdict(can_start=True, reasons=())


def test_every_missing_control_reason_comes_before_the_jha_reason() -> None:
    """Every reason that applies is shown, V2 before V3."""
    take5 = Take5(
        template=BOOKLET_TEMPLATE,
        answers=sample_answers(),
        hazards=tuple(
            Hazard(
                description=name,
                before=rate(BOOKLET_MATRIX, "Likely", "Minor"),
                controls=(),
                after=rate(BOOKLET_MATRIX, "Likely", "Minor"),
            )
            for name in ("Dust", "Moving tray")
        ),
    )

    assert verdict(take5).reasons == (
        "Say how you will control: Dust",
        "Say how you will control: Moving tray",
        "The risk is High (12). At 11 or more you need a JHA before you start. "
        "Talk to your supervisor.",
    )
