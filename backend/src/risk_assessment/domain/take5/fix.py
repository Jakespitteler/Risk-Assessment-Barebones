"""Which saved Take 5 a new one may fix (spec F3), and which have been fixed (spec F5).

Only a Take 5 that said Don't start yet can be fixed. The fix is a new Take 5 that
points back at it, so the first one is never changed.
"""

from collections.abc import Iterable
from uuid import UUID

from risk_assessment.domain.take5.draft import FieldError
from risk_assessment.domain.take5.saved import SavedTake5

FIXES_PATH: str = "fixes"
NOT_SAVED_MESSAGE: str = "The Take 5 this fixes could not be found."
NOTHING_TO_FIX_MESSAGE: str = "That Take 5 was Good to go, so there is nothing to fix."
NOT_FINISHED_MESSAGE: str = "That Take 5 isn't finished yet, so it can't be fixed."


def fixes_error(fixed: SavedTake5 | None) -> FieldError | None:
    """Say why a draft can't fix this saved Take 5, if it can't.

    Args:
        fixed: The saved Take 5 the draft says it fixes, or None if none is saved
            with that ID.

    Returns:
        The error to show, or None when the draft may fix it.
    """
    if fixed is None:
        return FieldError(path=FIXES_PATH, message=NOT_SAVED_MESSAGE)
    if fixed.verdict is None:
        return FieldError(path=FIXES_PATH, message=NOT_FINISHED_MESSAGE)
    if fixed.verdict.can_start:
        return FieldError(path=FIXES_PATH, message=NOTHING_TO_FIX_MESSAGE)
    return None


def offers_a_fix(saved: SavedTake5, fixed_by: UUID | None) -> bool:
    """Say whether a saved Take 5's result offers to fix it in a new Take 5.

    Only a Don't start yet is offered a fix, and only until it has one. After that
    its result links to the fix instead.

    Args:
        saved: The saved Take 5.
        fixed_by: The ID of the newest Take 5 that fixes it, or None.

    Returns:
        True when the result should offer a fix.
    """
    return fixes_error(saved) is None and fixed_by is None


def fixed_ids(take5s: Iterable[SavedTake5]) -> frozenset[UUID]:
    """Find the IDs of the Take 5s that these Take 5s fix.

    A Take 5 counts as fixed whatever the fix's own verdict, as its result screen
    says, and even while the fix's question is unanswered, so a second fix can't be
    started beside it. A fix is always saved after the Take 5 it fixes, so given
    every saved Take 5 this finds every fixed one. Given only some, it can miss a
    fix that isn't among them.

    Args:
        take5s: Saved Take 5s.

    Returns:
        The IDs that one of them fixes.
    """
    return frozenset(take5.fixes for take5 in take5s if take5.fixes is not None)
