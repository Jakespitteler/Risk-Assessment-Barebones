"""The fixed reasons a worker must not start (spec V1 to V3, P3)."""

from typing import ClassVar

from pydantic import BaseModel, ConfigDict

from risk_assessment.domain.questions import Answer, QuestionRole
from risk_assessment.domain.risk import RiskRating
from risk_assessment.domain.take5.take5 import Hazard, Take5


class Verdict(BaseModel):
    """Whether the job can start, and why not.

    Attributes:
        can_start: True for Good to go, False for Don't start yet.
        reasons: Every reason that applies, in the order of the rules (V1, then a
            paper card's blanks, P3, then V2 and V3).
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)
    can_start: bool
    reasons: tuple[str, ...]


NO_HAZARD_REASON: str = (
    "No hazard was written down. Think about what could hurt someone."
)


def verdict(take5: Take5) -> Verdict:
    """Work out the verdict for a Take 5 (spec V1 to V3).

    Args:
        take5: The rated Take 5.

    Returns:
        The verdict, with every reason that applies.
    """
    reasons: list[str] = _stop_answer_reasons(take5)
    if not take5.hazards:
        reasons.append(NO_HAZARD_REASON)
    reasons.extend(
        f"Rate the risk of: {_named(hazard)}"
        for hazard in take5.hazards
        if hazard.before is None
    )
    reasons.extend(
        f"Say how you will control: {_named(hazard)}"
        for hazard in take5.hazards
        if not hazard.controls
    )
    rating: RiskRating | None = take5.rating
    if rating is not None and take5.needs_jha:
        reasons.append(
            f"The risk is {rating.band} ({rating.score}). "
            f"At {take5.template.matrix.jha_threshold} or more you need a JHA before "
            "you start. Talk to your supervisor.",
        )
    return Verdict(can_start=not reasons, reasons=tuple(reasons))


def _named(hazard: Hazard) -> str:
    """Name a hazard in a reason by its words, or say it has none (a paper card, P3).

    Args:
        hazard: The hazard.

    Returns:
        Its description, or "the hazard with no description".
    """
    return hazard.description or "the hazard with no description"


def _stop_answer_reasons(take5: Take5) -> list[str]:
    """Give one reason for each stop question answered No, in the card's order (V1).

    The rule works from each question's role, never its wording, so it holds for any
    card. A hazard question answered Yes, or any N/A, is not a reason.

    Args:
        take5: The rated Take 5.

    Returns:
        The reasons, which may be none.
    """
    return [
        f"You answered No to: {question.text} Sort this out first."
        for question in take5.template.questions
        if question.role is QuestionRole.STOP
        and take5.answers.get(question.id) is Answer.NO
    ]
