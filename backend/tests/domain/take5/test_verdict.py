"""Worked examples for the saved verdict rules V2 and V3."""

import pytest

from risk_assessment.domain.controls import Control, ControlKind
from risk_assessment.domain.risk import rate
from risk_assessment.domain.take5.take5 import Hazard, Take5
from risk_assessment.domain.take5.template import BOOKLET_MATRIX, BOOKLET_TEMPLATE
from risk_assessment.domain.take5.verdict import Verdict, verdict


@pytest.mark.parametrize(
    ("before", "after", "has_control", "can_start", "reason_count"),
    [
        pytest.param(
            ("Possible", "Minor"),
            ("Unlikely", "Minor"),
            True,
            True,
            0,
            id="test_example_18",
        ),
        pytest.param(
            ("Possible", "Minor"),
            ("Possible", "Minor"),
            False,
            False,
            1,
            id="test_example_22",
        ),
        pytest.param(
            ("Likely", "Minor"),
            ("Likely", "Minor"),
            True,
            False,
            1,
            id="test_example_23",
        ),
        pytest.param(
            ("Almost Certain", "Low"),
            ("Almost Certain", "Low"),
            True,
            False,
            1,
            id="test_example_24",
        ),
        pytest.param(
            ("Possible", "Major"),
            ("Rare", "Major"),
            True,
            True,
            0,
            id="test_example_25",
        ),
    ],
)
def test_example_18_and_22_to_25_verdict(
    before: tuple[str, str],
    after: tuple[str, str],
    has_control: bool,
    can_start: bool,
    reason_count: int,
) -> None:
    """The after rating and missing controls decide the verdict, with no AI involved."""
    controls: tuple[Control, ...] = (
        (Control(description="Barricade the hazard", kind=ControlKind.BARRICADE),)
        if has_control
        else ()
    )
    take5 = Take5(
        template=BOOKLET_TEMPLATE,
        hazards=(
            Hazard(
                description="Example hazard",
                before=rate(BOOKLET_MATRIX, *before),
                controls=controls,
                after=rate(BOOKLET_MATRIX, *after),
            ),
        ),
    )
    result: Verdict = verdict(take5)
    assert result.can_start is can_start
    assert len(result.reasons) == reason_count
    if reason_count:
        assert ("JHA" in result.reasons[0]) is has_control


def test_every_missing_control_reason_precedes_the_jha_reason() -> None:
    """Show every applicable reason in V2 then V3 order."""
    take5 = Take5(
        template=BOOKLET_TEMPLATE,
        hazards=tuple(
            Hazard(
                description=name,
                before=rate(BOOKLET_MATRIX, "Likely", "Minor"),
                after=rate(BOOKLET_MATRIX, "Likely", "Minor"),
                controls=(),
            )
            for name in ("Dust", "Moving tray")
        ),
    )
    assert verdict(take5).reasons == (
        "Say how you will control: Dust",
        "Say how you will control: Moving tray",
        "The risk is High (12). At 11 or more you need a JHA before you start. "
        "Talk to your supervisor.",
    )
