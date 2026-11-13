"""Tests for checking a Take 5 the worker is still filling in."""

import pytest

from risk_assessment.domain.controls import ControlKind
from risk_assessment.domain.take5.draft import (
    FILL_IN_MESSAGE,
    HIGHER_AFTER_MESSAGE,
    NO_HAZARD_MESSAGE,
    NO_KIND_MESSAGE,
    ControlDraft,
    DraftCheck,
    FieldError,
    HazardDraft,
    RatingChoice,
    Take5Draft,
    check_draft,
)
from risk_assessment.domain.take5.take5 import Hazard
from risk_assessment.domain.take5.template import BOOKLET_TEMPLATE


def _hazard(
    before: tuple[str, str] = ("Possible", "Minor"),
    after: tuple[str, str] = ("Unlikely", "Minor"),
    controls: tuple[ControlDraft, ...] = (
        ControlDraft(description="Barricade the area", kind=ControlKind.BARRICADE),
    ),
) -> HazardDraft:
    """Make a complete hazard, rated 8 then 5 with one control unless told otherwise.

    Args:
        before: The likelihood and consequence before controls.
        after: The likelihood and consequence after controls.
        controls: The controls.

    Returns:
        The hazard as the phone would send it.
    """
    return HazardDraft(
        description="Moving wheel",
        before=RatingChoice(likelihood=before[0], consequence=before[1]),
        controls=controls,
        after=RatingChoice(likelihood=after[0], consequence=after[1]),
    )


def _draft(*hazards: HazardDraft) -> Take5Draft:
    """Make a complete draft.

    Args:
        *hazards: Its hazards. With none, it has one complete hazard.

    Returns:
        The draft as the phone would send it.
    """
    return Take5Draft(
        worker_name="Sam Example",
        job="Change tyre on LV12",
        location="Example workshop",
        hazards=hazards or (_hazard(),),
    )


def test_a_complete_draft_is_rated_and_can_be_submitted() -> None:
    """With nothing missing the check returns the rated Take 5."""
    check: DraftCheck = check_draft(_draft(), BOOKLET_TEMPLATE)

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
        FieldError(path="hazards", message=NO_HAZARD_MESSAGE),
    )
    assert check.assessment is None
    assert not check.can_submit


def test_example_14_no_hazards_cannot_be_submitted() -> None:
    """Every Take 5 has at least one hazard (R5)."""
    check: DraftCheck = check_draft(
        _draft().model_copy(update={"hazards": ()}), BOOKLET_TEMPLATE
    )

    assert check.errors == (FieldError(path="hazards", message=NO_HAZARD_MESSAGE),)


@pytest.mark.parametrize("field", ["worker_name", "job", "location"])
def test_an_answer_of_only_spaces_is_blank(field: str) -> None:
    """Spaces alone don't fill in a field."""
    check: DraftCheck = check_draft(
        _draft().model_copy(update={field: "   "}), BOOKLET_TEMPLATE
    )

    assert check.errors == (FieldError(path=field, message=FILL_IN_MESSAGE),)


def test_a_half_picked_rating_names_the_missing_half() -> None:
    """A likelihood without a consequence is not a rating, so no score is shown."""
    hazard: HazardDraft = _hazard().model_copy(
        update={"before": RatingChoice(likelihood="Possible")}
    )

    check: DraftCheck = check_draft(_draft(hazard), BOOKLET_TEMPLATE)

    assert check.errors == (
        FieldError(path="hazards.0.before.consequence", message="Pick a consequence."),
    )


def test_a_level_that_is_not_on_the_card_is_not_picked() -> None:
    """The phone can't send a level the matrix doesn't have."""
    hazard: HazardDraft = _hazard().model_copy(
        update={"after": RatingChoice(likelihood="Invented", consequence="Minor")}
    )

    check: DraftCheck = check_draft(_draft(hazard), BOOKLET_TEMPLATE)

    assert check.errors == (
        FieldError(path="hazards.0.after.likelihood", message="Pick a likelihood."),
    )


def test_a_control_needs_its_wording_and_its_kind() -> None:
    """Each half of a control is named beside its own field."""
    hazard: HazardDraft = _hazard(
        controls=(
            ControlDraft(description=" ", kind=ControlKind.PPE),
            ControlDraft(description="Gloves"),
        )
    )

    check: DraftCheck = check_draft(_draft(hazard), BOOKLET_TEMPLATE)

    assert check.errors == (
        FieldError(path="hazards.0.controls.0.description", message=FILL_IN_MESSAGE),
        FieldError(path="hazards.0.controls.1.kind", message=NO_KIND_MESSAGE),
    )


def test_example_15_controls_cannot_raise_the_score() -> None:
    """Unlikely / Minor (5) then Possible / Minor (8) can't be submitted (R6)."""
    hazard: HazardDraft = _hazard(
        before=("Unlikely", "Minor"), after=("Possible", "Minor")
    )

    check: DraftCheck = check_draft(_draft(hazard), BOOKLET_TEMPLATE)

    assert check.errors == (
        FieldError(path="hazards.0.after", message=HIGHER_AFTER_MESSAGE),
    )


def test_example_16_an_unchanged_score_is_allowed() -> None:
    """Possible / Minor (8) then Possible / Minor (8) is rated 8 Moderate (R6)."""
    hazard: HazardDraft = _hazard(after=("Possible", "Minor"))

    check: DraftCheck = check_draft(_draft(hazard), BOOKLET_TEMPLATE)

    assert check.assessment is not None
    assert (check.assessment.rating.score, check.assessment.rating.band) == (
        8,
        "Moderate",
    )


def test_example_17_with_no_controls_after_is_the_before_rating() -> None:
    """With no controls the after choice is ignored, so it is not rated again (R6)."""
    hazard: HazardDraft = _hazard(controls=()).model_copy(
        update={"after": RatingChoice()}
    )

    check: DraftCheck = check_draft(_draft(hazard), BOOKLET_TEMPLATE)

    assert check.assessment is not None
    rated: Hazard = check.assessment.hazards[0]
    assert rated.after == rated.before
    assert (check.assessment.rating.score, check.assessment.rating.band) == (
        8,
        "Moderate",
    )


def test_errors_on_a_later_hazard_carry_its_own_index() -> None:
    """The second hazard's gap is named against the second hazard."""
    incomplete: HazardDraft = _hazard().model_copy(update={"description": ""})

    check: DraftCheck = check_draft(_draft(_hazard(), incomplete), BOOKLET_TEMPLATE)

    assert check.errors == (
        FieldError(path="hazards.1.description", message=FILL_IN_MESSAGE),
    )


def test_answers_are_trimmed() -> None:
    """Spaces at either end are not kept."""
    hazard: HazardDraft = _hazard().model_copy(update={"description": "  Dust  "})

    check: DraftCheck = check_draft(_draft(hazard), BOOKLET_TEMPLATE)

    assert check.assessment is not None
    assert check.assessment.hazards[0].description == "Dust"
