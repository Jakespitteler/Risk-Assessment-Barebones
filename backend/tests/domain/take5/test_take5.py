"""Worked examples 11 to 17: the rating of a Take 5 and the effects of controls."""

import pytest
from pydantic import BaseModel

from risk_assessment.domain.questions import Answer
from risk_assessment.domain.risk import RiskCell, RiskMatrix, RiskRating, rate
from risk_assessment.domain.take5.take5 import Hazard, Take5
from risk_assessment.domain.take5.template import (
    BOOKLET_MATRIX,
    BOOKLET_TEMPLATE,
    Take5Template,
)
from tests.samples import BARRICADE, sample_answers, sample_hazard


def test_example_11_the_highest_after_rating_counts() -> None:
    """After scores 5 and 9 give the whole Take 5 a rating of 9 Moderate."""
    take5 = Take5(
        template=BOOKLET_TEMPLATE,
        answers=sample_answers(),
        hazards=(
            sample_hazard(("Possible", "Minor"), ("Unlikely", "Minor")),
            sample_hazard(("Possible", "Moderate"), ("Unlikely", "Moderate")),
        ),
    )
    assert take5.rating == rate(BOOKLET_MATRIX, "Unlikely", "Moderate")
    assert not take5.needs_jha


def test_example_12_one_high_after_rating_needs_a_jha() -> None:
    """One hazard remaining at 12 High is enough to need a JHA."""
    take5 = Take5(
        template=BOOKLET_TEMPLATE,
        answers=sample_answers(),
        hazards=(
            sample_hazard(("Possible", "Minor"), ("Unlikely", "Minor")),
            sample_hazard(("Likely", "Minor"), ("Likely", "Minor")),
        ),
    )
    assert take5.rating == rate(BOOKLET_MATRIX, "Likely", "Minor")
    assert take5.needs_jha


def test_example_13_after_not_before_decides_the_jha() -> None:
    """Reducing 18 Extreme to 10 High puts the Take 5 below the JHA threshold."""
    take5 = Take5(
        template=BOOKLET_TEMPLATE,
        answers=sample_answers(),
        hazards=(sample_hazard(("Possible", "Major"), ("Rare", "Major")),),
    )
    assert take5.rating == rate(BOOKLET_MATRIX, "Rare", "Major")
    assert not take5.needs_jha


def test_example_14_no_hazards_is_refused() -> None:
    """A Take 5 must contain at least one hazard, so it always has a rating."""
    with pytest.raises(ValueError, match="at least 1 item"):
        Take5(template=BOOKLET_TEMPLATE, answers=sample_answers(), hazards=())


def test_example_15_controls_cannot_raise_the_score() -> None:
    """An increase from 5 Low to 8 Moderate is refused."""
    with pytest.raises(ValueError, match="cannot make the after risk higher"):
        sample_hazard(("Unlikely", "Minor"), ("Possible", "Minor"))


def test_example_16_controls_can_leave_the_score_unchanged() -> None:
    """An unchanged score of 8 Moderate is valid and needs no JHA."""
    take5 = Take5(
        template=BOOKLET_TEMPLATE,
        answers=sample_answers(),
        hazards=(sample_hazard(("Possible", "Minor"), ("Possible", "Minor")),),
    )
    assert take5.rating == rate(BOOKLET_MATRIX, "Possible", "Minor")
    assert not take5.needs_jha


def test_example_17_no_controls_reuses_the_before_rating() -> None:
    """Without controls there is no second rating; 8 Moderate remains 8 Moderate."""
    before: RiskRating = rate(BOOKLET_MATRIX, "Possible", "Minor")
    hazard = Hazard(
        description="Example hazard",
        before=before,
        controls=(),
        after=before,
    )
    take5 = Take5(
        template=BOOKLET_TEMPLATE,
        answers=sample_answers(),
        hazards=(hazard,),
    )
    assert hazard.after is before
    assert take5.rating == before
    assert not take5.needs_jha


def test_no_controls_cannot_change_the_rating() -> None:
    """A lower second rating cannot disguise risk when no control was supplied."""
    with pytest.raises(ValueError, match="Without controls"):
        Hazard(
            description="Example hazard",
            controls=(),
            before=rate(BOOKLET_MATRIX, "Possible", "Minor"),
            after=rate(BOOKLET_MATRIX, "Unlikely", "Minor"),
        )


def test_the_highest_before_hazard_need_not_have_the_highest_after() -> None:
    """Choose the highest residual score, not the hazard that started worst."""
    take5 = Take5(
        template=BOOKLET_TEMPLATE,
        answers=sample_answers(),
        hazards=(
            sample_hazard(("Possible", "Major"), ("Unlikely", "Minor")),
            sample_hazard(("Possible", "Moderate"), ("Unlikely", "Moderate")),
        ),
    )
    assert take5.rating == rate(BOOKLET_MATRIX, "Unlikely", "Moderate")


def test_scoring_models_are_frozen() -> None:
    """A validated assessment and its nested values cannot be assigned new fields."""
    hazard: Hazard = sample_hazard(("Possible", "Minor"), ("Unlikely", "Minor"))
    take5 = Take5(
        template=BOOKLET_TEMPLATE,
        answers=sample_answers(),
        hazards=(hazard,),
    )
    values: tuple[tuple[BaseModel, str], ...] = (
        (take5, "hazards"),
        (hazard, "after"),
        (BARRICADE, "kind"),
        (BOOKLET_TEMPLATE, "matrix"),
    )
    for value, field_name in values:
        with pytest.raises(ValueError, match="frozen"):
            setattr(value, field_name, getattr(value, field_name))


def test_a_second_matrix_supplies_its_own_scales_bands_and_jha_threshold() -> None:
    """A two-by-two company's card is rated without any booklet-specific rules."""
    matrix = RiskMatrix(
        likelihoods=("Frequent", "Infrequent"),
        consequences=("Scratch", "Injury"),
        cells=(
            (RiskCell(score=4, band="Review"), RiskCell(score=8, band="Stop")),
            (RiskCell(score=2, band="Routine"), RiskCell(score=6, band="Review")),
        ),
        jha_threshold=6,
    )
    before: RiskRating = rate(matrix, "Frequent", "Injury")
    after: RiskRating = rate(matrix, "Infrequent", "Injury")
    take5 = Take5(
        template=Take5Template(name="Example company", matrix=matrix),
        hazards=(
            Hazard(
                description="Example hazard",
                before=before,
                controls=(BARRICADE,),
                after=after,
            ),
        ),
    )
    assert take5.rating == RiskRating(
        likelihood="Infrequent",
        consequence="Injury",
        score=6,
        band="Review",
    )
    assert take5.needs_jha
    assert not matrix.needs_jha(rate(matrix, "Frequent", "Scratch").score)


@pytest.mark.parametrize(("score", "band"), [(1, "Moderate"), (8, "Low")])
def test_a_supplied_rating_must_match_its_template(score: int, band: str) -> None:
    """Neither a forged score nor a forged band can override the template's lookup."""
    forged = RiskRating(
        likelihood="Possible",
        consequence="Minor",
        score=score,
        band=band,
    )
    with pytest.raises(ValueError, match="must match the template's matrix"):
        Take5(
            template=BOOKLET_TEMPLATE,
            answers=sample_answers(),
            hazards=(
                Hazard(
                    description="Example hazard",
                    before=forged,
                    controls=(),
                    after=forged,
                ),
            ),
        )


def test_a_take5_needs_an_answer_to_every_question_on_its_card() -> None:
    """A missing answer can't be rated, since the verdict needs every answer."""
    answers: dict[str, Answer] = sample_answers()
    del answers["plan"]

    with pytest.raises(ValueError, match="needs exactly one answer"):
        Take5(template=BOOKLET_TEMPLATE, answers=answers, hazards=(sample_hazard(),))


def test_a_take5_refuses_an_answer_to_a_question_its_card_does_not_ask() -> None:
    """An answer to a made-up question is never kept."""
    with pytest.raises(ValueError, match="needs exactly one answer"):
        Take5(
            template=BOOKLET_TEMPLATE,
            answers=sample_answers() | {"made_up": Answer.YES},
            hazards=(sample_hazard(),),
        )


def test_a_take5_on_a_card_with_no_questions_has_no_answers() -> None:
    """A Take 5 saved before the app asked questions still opens."""
    old_card: Take5Template = BOOKLET_TEMPLATE.model_copy(update={"questions": ()})

    take5 = Take5(template=old_card, hazards=(sample_hazard(),))

    assert take5.answers == {}
