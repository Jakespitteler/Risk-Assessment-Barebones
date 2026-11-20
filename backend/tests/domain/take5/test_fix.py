"""Tests for which saved Take 5 a new one may fix."""

from uuid import uuid4

import pytest

from risk_assessment.domain.take5.draft import FieldError
from risk_assessment.domain.take5.fix import (
    NOT_FINISHED_MESSAGE,
    NOT_SAVED_MESSAGE,
    NOTHING_TO_FIX_MESSAGE,
    fixes_error,
    offers_a_fix,
)
from risk_assessment.domain.take5.saved import SavedTake5
from risk_assessment.domain.take5.verdict import Verdict
from tests.samples import sample_saved_take5


def test_a_dont_start_yet_can_be_fixed() -> None:
    """A Take 5 that stopped the job is the only kind there is something to fix in."""
    stopped = Verdict(can_start=False, reasons=("Say how you will control: Wheel",))

    assert fixes_error(sample_saved_take5(stopped)) is None


def test_a_take5_that_is_not_saved_cannot_be_fixed() -> None:
    """An ID with no saved Take 5 behind it is refused on the `fixes` field."""
    assert fixes_error(None) == FieldError(path="fixes", message=NOT_SAVED_MESSAGE)


def test_a_good_to_go_cannot_be_fixed() -> None:
    """There is nothing to fix in a Take 5 that said Good to go."""
    good_to_go = Verdict(can_start=True, reasons=())

    assert fixes_error(sample_saved_take5(good_to_go)) == FieldError(
        path="fixes",
        message=NOTHING_TO_FIX_MESSAGE,
    )


def test_an_unfinished_take5_cannot_be_fixed_until_it_has_a_verdict() -> None:
    """A Take 5 whose question is unanswered has no verdict yet, so nothing to fix."""
    unfinished: SavedTake5 = sample_saved_take5().model_copy(
        update={"verdict": None, "finished_at": None},
    )

    assert fixes_error(unfinished) == FieldError(
        path="fixes",
        message=NOT_FINISHED_MESSAGE,
    )
    assert offers_a_fix(unfinished, None) is False


_STOPPED = Verdict(can_start=False, reasons=("Say how you will control: Wheel",))
_GOOD_TO_GO = Verdict(can_start=True, reasons=())


@pytest.mark.parametrize(
    ("verdict", "has_a_fix", "offered"),
    [(_STOPPED, False, True), (_STOPPED, True, False), (_GOOD_TO_GO, False, False)],
)
def test_a_fix_is_offered_only_for_a_dont_start_yet_with_no_fix_yet(
    verdict: Verdict,
    has_a_fix: bool,
    offered: bool,
) -> None:
    """Once fixed, the result links to its fix instead of offering another."""
    fixed_by = uuid4() if has_a_fix else None

    assert offers_a_fix(sample_saved_take5(verdict), fixed_by) is offered
