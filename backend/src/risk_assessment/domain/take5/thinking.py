"""Pure checks that ask the worker to think about the real job (T2 to T5)."""

from collections.abc import Iterable, Mapping

from risk_assessment.domain.controls import ControlKind
from risk_assessment.domain.questions import Answer, Question, QuestionRole
from risk_assessment.domain.risk import RiskMatrix, RiskRating
from risk_assessment.domain.wording import is_vague, word_count

VAGUE_CONTROL_MESSAGE: str = "Say what you'll actually do."
SHORT_JOB_MESSAGE: str = "Describe the job in at least four words."
UNLINKED_YES_MESSAGE: str = "Pick the hazard on your list that this is, or add it."
WEAK_CONTROLS_QUESTION: str = (
    "Everything here relies on people getting it right. "
    "Could you remove, isolate or barricade it?"
)


def control_wording_error(description: str) -> str | None:
    """Refuse a control that is nothing but a vague phrase (T2).

    Args:
        description: What the worker says they will do.

    Returns:
        The field's error message, or None when the wording is not vague.
    """
    return VAGUE_CONTROL_MESSAGE if is_vague(description) else None


def job_wording_error(description: str) -> str | None:
    """Require at least four words about the actual job (T4).

    Args:
        description: The worker's job description.

    Returns:
        The field's error message, or None when it has at least four words.
    """
    return SHORT_JOB_MESSAGE if word_count(description) < 4 else None


def weak_controls_question(
    before: RiskRating,
    kinds: tuple[ControlKind, ...],
    matrix: RiskMatrix,
) -> str | None:
    """Ask about stronger controls for a serious hazard with only weak controls (T3).

    Args:
        before: The hazard's rating before controls.
        kinds: The kinds picked for its controls.
        matrix: The card's matrix, whose JHA threshold defines a serious hazard.

    Returns:
        The question if at least one control exists and all are weak at or above
        the threshold; otherwise None. The after rating never decides this.
    """
    applies: bool = (
        matrix.needs_jha(before.score)
        and bool(kinds)
        and all(not kind.is_strong for kind in kinds)
    )
    return WEAK_CONTROLS_QUESTION if applies else None


def unlinked_yes_answers(
    questions: Iterable[Question],
    answers: Mapping[str, Answer],
    covered: Iterable[str],
) -> tuple[str, ...]:
    """Find each hazard question answered Yes that no hazard on the list covers (T5).

    Args:
        questions: The card's questions, in its order.
        answers: The worker's answers, by question ID.
        covered: The IDs of the questions the worker's hazards cover.

    Returns:
        The IDs of the hazard questions answered Yes with no hazard linked to them, in
        the card's order.
    """
    covered_ids: frozenset[str] = frozenset(covered)
    return tuple(
        question.id
        for question in questions
        if question.role is QuestionRole.HAZARD
        and answers.get(question.id) is Answer.YES
        and question.id not in covered_ids
    )
