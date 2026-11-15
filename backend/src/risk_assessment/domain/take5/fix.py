"""Which saved Take 5 a new one may fix (spec F3).

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
    """Find which of these Take 5s have been fixed by another one among them.

    A fix is always saved after the Take 5 it fixes, so a list that holds every
    Take 5 newer than the oldest one in it also holds every fix of them.

    Args:
        take5s: Saved Take 5s.

    Returns:
        The IDs of the Take 5s that one of them fixes.
    """
    return frozenset(take5.fixes for take5 in take5s if take5.fixes is not None)
