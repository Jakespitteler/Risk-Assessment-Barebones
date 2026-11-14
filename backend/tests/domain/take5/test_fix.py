"""Tests for which saved Take 5 a new one may fix."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from risk_assessment.domain.controls import Control, ControlKind
from risk_assessment.domain.risk import rate
from risk_assessment.domain.take5.draft import FieldError
from risk_assessment.domain.take5.fix import (
    NOT_SAVED_MESSAGE,
    NOTHING_TO_FIX_MESSAGE,
    fixes_error,
    offers_a_fix,
)
from risk_assessment.domain.take5.saved import SavedTake5
from risk_assessment.domain.take5.take5 import Hazard
from risk_assessment.domain.take5.template import BOOKLET_MATRIX, BOOKLET_TEMPLATE
from risk_assessment.domain.take5.verdict import Verdict


def _saved(verdict: Verdict) -> SavedTake5:
    """Make a saved Take 5 with one controlled hazard and the given verdict.

    Args:
        verdict: The verdict it was saved with.

    Returns:
        The saved Take 5.
    """
    now: datetime = datetime(2026, 11, 13, 7, 30, tzinfo=UTC)
    return SavedTake5(
        template=BOOKLET_TEMPLATE,
        hazards=(
            Hazard(
                description="Moving wheel",
                before=rate(BOOKLET_MATRIX, "Possible", "Minor"),
                controls=(
                    Control(
                        description="Barricade the area", kind=ControlKind.BARRICADE
                    ),
                ),
                after=rate(BOOKLET_MATRIX, "Unlikely", "Minor"),
            ),
        ),
        id=uuid4(),
        created_at=now,
        finished_at=now,
        worker_name="Sam Example",
        job="Change tyre on LV12",
        location="Example workshop",
        verdict=verdict,
    )


def test_a_dont_start_yet_can_be_fixed() -> None:
    """A Take 5 that stopped the job is the only kind there is something to fix in."""
    stopped = Verdict(can_start=False, reasons=("Say how you will control: Wheel",))

    assert fixes_error(_saved(stopped)) is None


def test_a_take5_that_is_not_saved_cannot_be_fixed() -> None:
    """An ID with no saved Take 5 behind it is refused on the `fixes` field."""
    assert fixes_error(None) == FieldError(path="fixes", message=NOT_SAVED_MESSAGE)


def test_a_good_to_go_cannot_be_fixed() -> None:
    """There is nothing to fix in a Take 5 that said Good to go."""
    good_to_go = Verdict(can_start=True, reasons=())

    assert fixes_error(_saved(good_to_go)) == FieldError(
        path="fixes", message=NOTHING_TO_FIX_MESSAGE
    )


_STOPPED = Verdict(can_start=False, reasons=("Say how you will control: Wheel",))
_GOOD_TO_GO = Verdict(can_start=True, reasons=())


@pytest.mark.parametrize(
    ("verdict", "has_a_fix", "offered"),
    [(_STOPPED, False, True), (_STOPPED, True, False), (_GOOD_TO_GO, False, False)],
)
def test_a_fix_is_offered_only_for_a_dont_start_yet_with_no_fix_yet(
    verdict: Verdict, has_a_fix: bool, offered: bool
) -> None:
    """Once fixed, the result links to its fix instead of offering another."""
    fixed_by = uuid4() if has_a_fix else None

    assert offers_a_fix(_saved(verdict), fixed_by) is offered
