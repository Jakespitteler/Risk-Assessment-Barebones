"""Tests for checking a Take 5 the worker is still filling in."""

import pytest

from risk_assessment.domain.controls import ControlKind
from risk_assessment.domain.questions import Answer
from risk_assessment.domain.take5.draft import (
    FILL_IN_MESSAGE,
    HIGHER_AFTER_MESSAGE,
    NO_ANSWER_MESSAGE,
    NO_CONTROLS_WARNING,
    NO_HAZARD_MESSAGE,
    NO_KIND_MESSAGE,
    STOP_ANSWER_WARNING,
    ControlDraft,
    DraftCheck,
    FieldError,
    FieldWarning,
    HazardDraft,
    RatingChoice,
    Take5Draft,
    check_draft,
)
from risk_assessment.domain.take5.take5 import Hazard
from risk_assessment.domain.take5.template import BOOKLET_TEMPLATE
from risk_assessment.domain.take5.thinking import UNLINKED_YES_MESSAGE
from tests.samples import sample_answers, sample_draft, sample_hazard_draft


def test_a_complete_draft_is_rated_and_can_be_submitted() -> None:
    """With nothing missing the check returns the rated Take 5."""
    check: DraftCheck = check_draft(sample_draft(), BOOKLET_TEMPLATE)

    assert check.errors == ()
    assert check.can_submit
    assert check.assessment is not None
    assert check.assessment.rating.score == 5
    assert check.assessment.rating.band == "Low"


def test_an_empty_draft_names_every_missing_field_and_nothing_else() -> None:
    """A blank form is told what is missing, in the order of the form."""
    check: DraftCheck = check_draft(Take5Draft(), BOOKLET_TEMPLATE)

    assert check.errors == (
        FieldError(path="worker_name", message=FILL_IN_MESSAGE),
        FieldError(path="job", message=FILL_IN_MESSAGE),
        FieldError(path="location", message=FILL_IN_MESSAGE),
        *(
            FieldError(path=f"answers.{question.id}", message=NO_ANSWER_MESSAGE)
            for question in BOOKLET_TEMPLATE.questions
        ),
        FieldError(path="hazards", message=NO_HAZARD_MESSAGE),
    )
    assert check.assessment is None
    assert not check.can_submit


def test_the_answers_are_kept_with_the_rated_take5() -> None:
    """Each question's answer reaches the assessment, so the verdict can use it."""
    answers: dict[str, Answer] = sample_answers(permits=Answer.NOT_APPLICABLE)
    check: DraftCheck = check_draft(
        sample_draft().model_copy(update={"answers": answers}),
        BOOKLET_TEMPLATE,
    )

    assert check.assessment is not None
    assert check.assessment.answers == answers


def test_an_unanswered_question_is_named_by_its_id() -> None:
    """A question with no answer is a gap beside that question, and nothing else is."""
    answers: dict[str, Answer] = sample_answers()
    del answers["permits"]

    check: DraftCheck = check_draft(
        sample_draft().model_copy(update={"answers": answers}),
        BOOKLET_TEMPLATE,
    )

    assert check.errors == (
        FieldError(path="answers.permits", message=NO_ANSWER_MESSAGE),
    )
    assert check.assessment is None


def test_an_answer_to_a_question_the_card_does_not_ask_is_not_kept() -> None:
    """Only the card's own questions are answered, so nothing else is saved."""
    check: DraftCheck = check_draft(
        sample_draft().model_copy(
            update={"answers": sample_answers() | {"made_up": Answer.NO}},
        ),
        BOOKLET_TEMPLATE,
    )

    assert check.assessment is not None
    assert check.assessment.answers == sample_answers()


def test_a_no_to_a_stop_question_is_a_warning_that_still_lets_it_submit() -> None:
    """A No will stop the job (V1), so the review is told, but it is allowed."""
    check: DraftCheck = check_draft(
        sample_draft().model_copy(
            update={
                "answers": sample_answers(
                    permits=Answer.NO,
                    ppe=Answer.NOT_APPLICABLE,
                    heights=Answer.NO,
                ),
            },
        ),
        BOOKLET_TEMPLATE,
    )

    assert check.warnings == (
        FieldWarning(path="answers.permits", message=STOP_ANSWER_WARNING),
    )
    assert check.can_submit


def test_example_14_no_hazards_cannot_be_submitted() -> None:
    """Every Take 5 has at least one hazard (R5)."""
    check: DraftCheck = check_draft(
        sample_draft().model_copy(update={"hazards": ()}),
        BOOKLET_TEMPLATE,
    )

    assert check.errors == (FieldError(path="hazards", message=NO_HAZARD_MESSAGE),)


@pytest.mark.parametrize("field", ["worker_name", "job", "location"])
def test_an_answer_of_only_spaces_is_blank(field: str) -> None:
    """Spaces alone don't fill in a field."""
    check: DraftCheck = check_draft(
        sample_draft().model_copy(update={field: "   "}),
        BOOKLET_TEMPLATE,
    )

    assert check.errors == (FieldError(path=field, message=FILL_IN_MESSAGE),)


def test_a_half_picked_rating_names_the_missing_half() -> None:
    """A likelihood without a consequence is not a rating, so no score is shown."""
    hazard: HazardDraft = sample_hazard_draft().model_copy(
        update={"before": RatingChoice(likelihood="Possible")},
    )

    check: DraftCheck = check_draft(sample_draft(hazard), BOOKLET_TEMPLATE)

    assert check.errors == (
        FieldError(path="hazards.0.before.consequence", message="Pick a consequence."),
    )


def test_a_level_that_is_not_on_the_card_is_not_picked() -> None:
    """The phone can't send a level the matrix doesn't have."""
    hazard: HazardDraft = sample_hazard_draft().model_copy(
        update={"after": RatingChoice(likelihood="Invented", consequence="Minor")},
    )

    check: DraftCheck = check_draft(sample_draft(hazard), BOOKLET_TEMPLATE)

    assert check.errors == (
        FieldError(path="hazards.0.after.likelihood", message="Pick a likelihood."),
    )


def test_a_control_needs_its_wording_and_its_kind() -> None:
    """Each half of a control is named beside its own field."""
    hazard: HazardDraft = sample_hazard_draft(
        controls=(
            ControlDraft(description=" ", kind=ControlKind.PPE),
            ControlDraft(description="Gloves"),
        ),
    )

    check: DraftCheck = check_draft(sample_draft(hazard), BOOKLET_TEMPLATE)

    assert check.errors == (
        FieldError(path="hazards.0.controls.0.description", message=FILL_IN_MESSAGE),
        FieldError(path="hazards.0.controls.1.kind", message=NO_KIND_MESSAGE),
    )


def test_example_15_controls_cannot_raise_the_score() -> None:
    """Unlikely / Minor (5) then Possible / Minor (8) can't be submitted (R6)."""
    hazard: HazardDraft = sample_hazard_draft(
        before=("Unlikely", "Minor"),
        after=("Possible", "Minor"),
    )

    check: DraftCheck = check_draft(sample_draft(hazard), BOOKLET_TEMPLATE)

    assert check.errors == (
        FieldError(path="hazards.0.after", message=HIGHER_AFTER_MESSAGE),
    )


def test_example_16_an_unchanged_score_is_allowed() -> None:
    """Possible / Minor (8) then Possible / Minor (8) is rated 8 Moderate (R6)."""
    hazard: HazardDraft = sample_hazard_draft(after=("Possible", "Minor"))

    check: DraftCheck = check_draft(sample_draft(hazard), BOOKLET_TEMPLATE)

    assert check.assessment is not None
    assert (check.assessment.rating.score, check.assessment.rating.band) == (
        8,
        "Moderate",
    )


def test_example_17_with_no_controls_after_is_the_before_rating() -> None:
    """With no controls the after choice is ignored, so it is not rated again (R6)."""
    hazard: HazardDraft = sample_hazard_draft(controls=()).model_copy(
        update={"after": RatingChoice()},
    )

    check: DraftCheck = check_draft(sample_draft(hazard), BOOKLET_TEMPLATE)

    assert check.assessment is not None
    rated: Hazard = check.assessment.hazards[0]
    assert rated.after == rated.before
    assert (check.assessment.rating.score, check.assessment.rating.band) == (
        8,
        "Moderate",
    )


def test_example_17_a_hazard_with_no_controls_is_warned_about() -> None:
    """The warning says the job will be stopped (V2), and it never blocks submitting."""
    hazard: HazardDraft = sample_hazard_draft(controls=()).model_copy(
        update={"after": RatingChoice()},
    )

    check: DraftCheck = check_draft(sample_draft(hazard), BOOKLET_TEMPLATE)

    assert check.warnings == (
        FieldWarning(path="hazards.0.controls", message=NO_CONTROLS_WARNING),
    )
    assert check.can_submit
    assert NO_CONTROLS_WARNING == "No controls: you'll be told not to start."


def test_a_hazard_with_controls_gets_no_warning() -> None:
    """Example 18's controlled hazard has nothing to warn about."""
    assert check_draft(sample_draft(), BOOKLET_TEMPLATE).warnings == ()


def test_each_warning_is_on_its_own_hazard() -> None:
    """Only the second hazard has no controls, so only it is warned about."""
    uncontrolled: HazardDraft = sample_hazard_draft(controls=())

    check: DraftCheck = check_draft(
        sample_draft(sample_hazard_draft(), uncontrolled),
        BOOKLET_TEMPLATE,
    )

    assert [warning.path for warning in check.warnings] == ["hazards.1.controls"]


def test_a_draft_with_gaps_is_still_warned_about() -> None:
    """A warning comes with the errors, so the worker hears about it on any page."""
    blank: HazardDraft = HazardDraft()

    check: DraftCheck = check_draft(sample_draft(blank), BOOKLET_TEMPLATE)

    assert not check.can_submit
    assert [warning.path for warning in check.warnings] == ["hazards.0.controls"]


def test_errors_on_a_later_hazard_carry_its_own_index() -> None:
    """The second hazard's gap is named against the second hazard."""
    incomplete: HazardDraft = sample_hazard_draft().model_copy(
        update={"description": ""},
    )

    check: DraftCheck = check_draft(
        sample_draft(sample_hazard_draft(), incomplete),
        BOOKLET_TEMPLATE,
    )

    assert check.errors == (
        FieldError(path="hazards.1.description", message=FILL_IN_MESSAGE),
    )


def test_answers_are_trimmed() -> None:
    """Spaces at either end are not kept."""
    hazard: HazardDraft = sample_hazard_draft().model_copy(
        update={"description": "  Dust  "},
    )

    check: DraftCheck = check_draft(sample_draft(hazard), BOOKLET_TEMPLATE)

    assert check.assessment is not None
    assert check.assessment.hazards[0].description == "Dust"


def _heights_yes(*hazards: HazardDraft) -> Take5Draft:
    """Make the sample draft with "Will I be working at heights?" answered Yes.

    Args:
        *hazards: Its hazards. With none, it has the sample hazard, linked to nothing.

    Returns:
        The draft.
    """
    return sample_draft(*hazards).model_copy(
        update={"answers": sample_answers(heights=Answer.YES)},
    )


def test_example_65_a_yes_with_no_hazard_linked_cannot_be_submitted() -> None:
    """T5: the gap is named beside the question, on the hazard check page."""
    check: DraftCheck = check_draft(_heights_yes(), BOOKLET_TEMPLATE)

    assert check.errors == (
        FieldError(path="answers.heights", message=UNLINKED_YES_MESSAGE),
    )
    assert not check.can_submit


def test_example_66_a_yes_with_a_hazard_linked_is_saved_with_the_link() -> None:
    """T5: picking "Fall from the tray" for the heights question is enough."""
    fall: HazardDraft = sample_hazard_draft().model_copy(
        update={"description": "Fall from the tray", "covers": ("heights",)},
    )

    check: DraftCheck = check_draft(_heights_yes(fall), BOOKLET_TEMPLATE)

    assert check.errors == ()
    assert check.assessment is not None
    assert check.assessment.hazards[0].covers == ("heights",)


def test_example_69_a_link_to_a_question_now_answered_no_is_not_saved() -> None:
    """T5: the phone keeps the link, but only a link to a Yes is saved."""
    fall: HazardDraft = sample_hazard_draft().model_copy(
        update={"covers": ("heights",)},
    )

    check: DraftCheck = check_draft(sample_draft(fall), BOOKLET_TEMPLATE)

    assert check.errors == ()
    assert check.assessment is not None
    assert check.assessment.hazards[0].covers == ()


def test_a_link_to_a_question_the_card_does_not_ask_is_not_saved() -> None:
    """Only the card's hazard questions answered Yes are kept, each once."""
    fall: HazardDraft = sample_hazard_draft().model_copy(
        update={"covers": ("made_up", "heights", "permits", "heights")},
    )

    check: DraftCheck = check_draft(_heights_yes(fall), BOOKLET_TEMPLATE)

    assert check.assessment is not None
    assert check.assessment.hazards[0].covers == ("heights",)
