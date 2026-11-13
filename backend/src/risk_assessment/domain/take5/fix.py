"""Which saved Take 5 a new one may fix (spec F3).

Only a Take 5 that said Don't start yet can be fixed. The fix is a new Take 5 that
points back at it, so the first one is never changed.
"""

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
