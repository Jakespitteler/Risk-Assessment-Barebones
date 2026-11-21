"""Hazards, answers and the rating of a whole Take 5 (spec rules R4 to R6, P1 to P3)."""

from collections.abc import Mapping
from enum import StrEnum
from typing import ClassVar, Self

from pydantic import BaseModel, ConfigDict, model_validator

from risk_assessment.domain.controls import Control
from risk_assessment.domain.questions import Answer, QuestionRole
from risk_assessment.domain.risk import RiskRating, rate
from risk_assessment.domain.take5.template import Take5Template


class HazardFlag(StrEnum):
    """What the hazard check (T6) said was wrong with a hazard's words."""

    VAGUE = "vague"
    STOCK = "stock"
    UNFIT = "unfit"


class Hazard(BaseModel):
    """One hazard rated before and after controls, using ratings from `rate()`.

    Without controls, reuse the before rating as the after rating; no second rating
    is needed. Description, ratings and controls are immutable once constructed.
    A rating is None only on a paper card where it was left blank (P1); `Take5`
    refuses a None rating on any other Take 5.
    `covers` holds the IDs of the hazard questions answered Yes that the worker linked
    to this hazard (T5); it is empty for a Take 5 saved before links were kept.
    `kept_flag` is what the hazard check still said about its words when the Take 5
    was submitted, so the worker kept them after the nudge (T6, task 0037); None when
    nothing was flagged, or for a Take 5 saved before flags were kept.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    description: str
    before: RiskRating | None
    controls: tuple[Control, ...]
    after: RiskRating | None
    weak_controls_reason: str = ""
    covers: tuple[str, ...] = ()
    kept_flag: HazardFlag | None = None

    @property
    def counted_rating(self) -> RiskRating | None:
        """The rating the hazard counts at: after controls, else before (R4, P2).

        Returns:
            The after rating, or on a paper card with no after rating the before
            rating, or None when neither was given.
        """
        return self.after if self.after is not None else self.before


class Take5(BaseModel):
    """The answers, hazards and template needed to give a Take 5 its verdict.

    `SavedTake5` adds the job, the worker and the rest of the completed card. Ratings
    must match this template, so a caller cannot supply a different score or band.

    A paper card (P1) is kept as written: it may leave answers, ratings and control
    kinds blank and have no hazards. Every other Take 5 must have them all.

    Attributes:
        template: The card it was filled in on.
        answers: The answer to each of the template's questions, by question ID.
            Empty for a Take 5 saved before the app asked them, whose template has no
            questions. A paper card may leave some out.
        hazards: The rated hazards, at least one unless it is a paper card.
        from_paper: True when it was photographed off a paper card (task 0033).
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    template: Take5Template
    answers: Mapping[str, Answer] = {}
    hazards: tuple[Hazard, ...] = ()
    from_paper: bool = False

    @model_validator(mode="after")
    def _every_question_has_one_answer(self) -> Self:
        """Refuse an answer to a question the card doesn't ask, or a missing one.

        A paper card may leave a question unanswered (P1).
        """
        question_ids: set[str] = {question.id for question in self.template.questions}
        if not set(self.answers) <= question_ids:
            raise ValueError("Every answer must be to a question on the card.")
        if not self.from_paper and set(self.answers) != question_ids:
            raise ValueError("Every question on the card needs exactly one answer.")
        return self

    @model_validator(mode="after")
    def _only_a_paper_card_has_blanks(self) -> Self:
        """Refuse no hazards, or a blank rating or kind, except on paper (F2, P1)."""
        if self.from_paper:
            return self
        if not self.hazards:
            raise ValueError("A Take 5 needs at least one hazard.")
        for hazard in self.hazards:
            if hazard.before is None or hazard.after is None:
                raise ValueError("Every hazard needs a rating before and after.")
            if any(control.kind is None for control in hazard.controls):
                raise ValueError("Every control needs a kind.")
        return self

    @model_validator(mode="after")
    def _controls_cannot_raise_or_invent_a_reduction(self) -> Self:
        """Refuse higher after risk, or a changed rating without controls (R6).

        A paper card is kept as written, so it is not checked (P1).
        """
        if self.from_paper:
            return self
        for hazard in self.hazards:
            if hazard.before is None or hazard.after is None:
                continue
            if not hazard.controls and hazard.after != hazard.before:
                raise ValueError(
                    "Without controls, the after rating must be the before rating.",
                )
            if hazard.after.score > hazard.before.score:
                raise ValueError(
                    "Controls cannot make the after risk higher than before.",
                )
        return self

    @model_validator(mode="after")
    def _links_name_hazard_questions_answered_yes(self) -> Self:
        """Refuse a link to anything but a hazard question answered Yes (T5)."""
        linkable_ids: set[str] = {
            question.id
            for question in self.template.questions
            if question.role is QuestionRole.HAZARD
            and self.answers.get(question.id) is Answer.YES
        }
        for hazard in self.hazards:
            if not set(hazard.covers) <= linkable_ids:
                raise ValueError(
                    "A hazard can only cover the card's hazard questions answered Yes.",
                )
        return self

    @model_validator(mode="after")
    def _ratings_use_the_template_matrix(self) -> Self:
        """Check each before and after rating against the template's matrix."""
        for hazard in self.hazards:
            for rating in (hazard.before, hazard.after):
                if rating is None:
                    continue
                expected: RiskRating = rate(
                    self.template.matrix,
                    rating.likelihood,
                    rating.consequence,
                )
                if rating != expected:
                    raise ValueError(
                        "Every hazard rating must match the template's matrix.",
                    )
        return self

    @property
    def rating(self) -> RiskRating | None:
        """Return the highest after rating across the hazards (R4, R5, P2).

        Returns:
            The highest rating each hazard counts at, or None on a paper card with no
            rated hazard.
        """
        ratings: list[RiskRating] = [
            hazard.counted_rating
            for hazard in self.hazards
            if hazard.counted_rating is not None
        ]
        return max(ratings, key=lambda rating: rating.score, default=None)

    @property
    def needs_jha(self) -> bool:
        """Apply this template's JHA threshold to the Take 5's after rating (R3, R4)."""
        rating: RiskRating | None = self.rating
        return rating is not None and self.template.matrix.needs_jha(rating.score)
