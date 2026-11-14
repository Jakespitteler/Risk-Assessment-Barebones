"""The fixed reasons a worker must not start (spec V1 to V3)."""

from typing import ClassVar

from pydantic import BaseModel, ConfigDict

from risk_assessment.domain.questions import Answer, QuestionRole
from risk_assessment.domain.take5.take5 import Take5


class Verdict(BaseModel):
    """Whether the job can start, and why not.

    Attributes:
        can_start: True for Good to go, False for Don't start yet.
        reasons: Every reason that applies, in the order of the rules (V1, V2, then
            V3).
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)
    can_start: bool
    reasons: tuple[str, ...]


def verdict(take5: Take5) -> Verdict:
    """Work out the verdict for a Take 5 (spec V1 to V3).

    Args:
        take5: The rated Take 5.

    Returns:
        The verdict, with every reason that applies.
    """
    reasons: list[str] = _stop_answer_reasons(take5)
    reasons.extend(
        f"Say how you will control: {hazard.description}"
        for hazard in take5.hazards
        if not hazard.controls
    )
    if take5.needs_jha:
        reasons.append(
            f"The risk is {take5.rating.band} ({take5.rating.score}). "
            f"At {take5.template.matrix.jha_threshold} or more you need a JHA before "
            "you start. Talk to your supervisor.",
        )
    return Verdict(can_start=not reasons, reasons=tuple(reasons))


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
        and take5.answers[question.id] is Answer.NO
    ]
