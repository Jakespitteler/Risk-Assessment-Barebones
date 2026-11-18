"""Tests for the booklet's card: its fourteen questions, word for word (spec F2)."""

import pytest

from risk_assessment.domain.questions import Question, QuestionRole
from risk_assessment.domain.take5.template import (
    BOOKLET_MATRIX,
    BOOKLET_TEMPLATE,
    Take5Template,
)
from risk_assessment.domain.take5.thinking import hazard_wording_nudge

SPEC_STOP_QUESTIONS: tuple[str, ...] = (
    "Do you understand the task scope?",
    "Does a procedure exist?",
    "Do you understand the steps required to do the task?",
    "Are tools and equipment in good order?",
    "Do you have the correct PPE?",
    "Do you have the necessary permits?",
    "Have you got a clear plan in mind?",
)
SPEC_HAZARD_QUESTIONS: tuple[str, ...] = (
    "Will I be operating equipment with the guards removed?",
    "Am I or others at risk from the operation of vehicles or mobile equipment?",
    "Does the task involve hazardous materials?",
    "Will I be performing a task without a specific isolation procedure?",
    "Will I be working at heights?",
    "Will I be impacted by other activity in the vicinity?",
    "Other environmental and/or H&S hazards?",
)


def test_the_booklet_asks_the_specs_seven_stop_questions_first() -> None:
    """The think-through questions are the card's, in order, each a stop question."""
    stop_questions: tuple[Question, ...] = BOOKLET_TEMPLATE.questions[:7]

    assert tuple(question.text for question in stop_questions) == SPEC_STOP_QUESTIONS
    assert {question.role for question in stop_questions} == {QuestionRole.STOP}


def test_the_booklet_asks_the_specs_seven_hazard_questions_last() -> None:
    """The hazard questions are the card's, in its order, each a hazard question."""
    hazard_questions: tuple[Question, ...] = BOOKLET_TEMPLATE.questions[7:]

    assert (
        tuple(question.text for question in hazard_questions) == SPEC_HAZARD_QUESTIONS
    )
    assert {question.role for question in hazard_questions} == {QuestionRole.HAZARD}


def test_a_card_cannot_have_two_questions_with_one_id() -> None:
    """Answers are kept by question ID, so each ID must be used once."""
    with pytest.raises(ValueError, match="its own ID"):
        Take5Template(
            name="Example card",
            questions=(
                Question(id="gate", text="Is the gate shut?", role=QuestionRole.STOP),
                Question(id="gate", text="Is the gate open?", role=QuestionRole.HAZARD),
            ),
            matrix=BOOKLET_MATRIX,
        )


def test_a_question_id_cannot_hold_a_full_stop() -> None:
    """An ID goes in a dotted path, `answers.<id>`, so a full stop would split it."""
    with pytest.raises(ValueError, match="pattern"):
        Question(id="gate.keys", text="Is the gate shut?", role=QuestionRole.STOP)


SPEC_HAZARD_EXAMPLES: tuple[str, ...] = (
    "Hand caught in the conveyor tail pulley with the guard off",
    "Hit by a haul truck at the crib hut crossing",
    "Battery acid splashed in my eyes while topping up the cells",
    "Feeder starts up while I am clearing the chute",
    "Fall from the trailer deck while strapping the load",
    "Struck by rock from the excavator loading on the bench above",
    "Heat stress from working all afternoon in full sun",
)


def test_each_hazard_question_has_the_specs_example() -> None:
    """The nudge's examples are the ones the spec lists, in the card's order (T6)."""
    hazard_questions: tuple[Question, ...] = BOOKLET_TEMPLATE.questions[7:]

    assert (
        tuple(question.example for question in hazard_questions) == SPEC_HAZARD_EXAMPLES
    )


def test_no_example_would_itself_be_nudged() -> None:
    """Every example has at least as many words as a hazard needs (T6)."""
    assert BOOKLET_TEMPLATE.specific_hazard_words == 6
    assert all(
        hazard_wording_nudge(example, "", BOOKLET_TEMPLATE.specific_hazard_words)
        is None
        for example in SPEC_HAZARD_EXAMPLES
    )
