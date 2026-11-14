"""Hazards and the rating of a whole Take 5 (spec rules R4 to R6)."""

from typing import ClassVar, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from risk_assessment.domain.controls import Control
from risk_assessment.domain.risk import RiskRating, rate
from risk_assessment.domain.take5.template import Take5Template


class Hazard(BaseModel):
    """One hazard rated before and after controls, using ratings from `rate()`.

    Without controls, reuse the before rating as the after rating; no second rating
    is needed. Description, ratings and controls are immutable once constructed.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    description: str
    before: RiskRating
    controls: tuple[Control, ...]
    after: RiskRating

    @model_validator(mode="after")
    def _controls_cannot_raise_or_invent_a_reduction(self) -> Self:
        """Refuse higher after risk, or any changed rating without controls (R6)."""
        if not self.controls and self.after != self.before:
            raise ValueError(
                "Without controls, the after rating must be the before rating.",
            )
        if self.after.score > self.before.score:
            raise ValueError("Controls cannot make the after risk higher than before.")
        return self


class Take5(BaseModel):
    """The hazards and template needed to rate a Take 5.

    Later tasks add the job, the worker and the rest of the completed card. Ratings
    must match this template, so a caller cannot supply a different score or band.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    template: Take5Template
    hazards: tuple[Hazard, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _ratings_use_the_template_matrix(self) -> Self:
        """Check each before and after rating against the template's matrix."""
        for hazard in self.hazards:
            for rating in (hazard.before, hazard.after):
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
    def rating(self) -> RiskRating:
        """Return the highest after rating across the hazards (R4, R5)."""
        return max(
            (hazard.after for hazard in self.hazards),
            key=lambda rating: rating.score,
        )

    @property
    def needs_jha(self) -> bool:
        """Apply this template's JHA threshold to the Take 5's after rating (R3, R4)."""
        return self.template.matrix.needs_jha(self.rating.score)
