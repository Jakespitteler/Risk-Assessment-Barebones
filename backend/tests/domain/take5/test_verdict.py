"""Worked examples 18 and 22 to 25: the verdict rules V2 and V3, word for word."""

from risk_assessment.domain.controls import Control, ControlKind
from risk_assessment.domain.risk import rate
from risk_assessment.domain.take5.take5 import Hazard, Take5
from risk_assessment.domain.take5.template import BOOKLET_MATRIX, BOOKLET_TEMPLATE
from risk_assessment.domain.take5.verdict import Verdict, verdict

_BARRICADE: tuple[Control, ...] = (
    Control(description="Barricade the hazard", kind=ControlKind.BARRICADE),
)


def _take5(
    before: tuple[str, str] = ("Possible", "Minor"),
    after: tuple[str, str] = ("Unlikely", "Minor"),
    controls: tuple[Control, ...] = _BARRICADE,
) -> Take5:
    """Make the spec's default Take 5 for these examples: 8 then 5, with a barricade.

    Args:
        before: The likelihood and consequence before controls.
        after: The likelihood and consequence after controls. Ignored with no controls.
        controls: The controls.

    Returns:
        The rated Take 5.
    """
    return Take5(
        template=BOOKLET_TEMPLATE,
        hazards=(
            Hazard(
                description="Moving wheel",
                before=rate(BOOKLET_MATRIX, *before),
                controls=controls,
                after=rate(BOOKLET_MATRIX, *(after if controls else before)),
            ),
        ),
    )


def test_example_18_nothing_different_is_good_to_go() -> None:
    """No reason applies, so the job can start."""
    assert verdict(_take5()) == Verdict(can_start=True, reasons=())


def test_example_22_a_hazard_with_no_controls_says_how_to_control_it() -> None:
    """V2 names the hazard that has no controls."""
    assert verdict(_take5(controls=())) == Verdict(
        can_start=False,
        reasons=("Say how you will control: Moving wheel",),
    )


def test_example_23_a_rating_of_12_needs_a_jha() -> None:
    """V3 applies at 11 or more."""
    result: Verdict = verdict(
        _take5(before=("Likely", "Minor"), after=("Likely", "Minor")),
    )

    assert result == Verdict(
        can_start=False,
        reasons=(
            "The risk is High (12). At 11 or more you need a JHA before you start. "
            "Talk to your supervisor.",
        ),
    )


def test_example_24_a_rating_of_exactly_11_needs_a_jha() -> None:
    """V3 applies at exactly the threshold."""
    result: Verdict = verdict(
        _take5(before=("Almost Certain", "Low"), after=("Almost Certain", "Low")),
    )

    assert result == Verdict(
        can_start=False,
        reasons=(
            "The risk is High (11). At 11 or more you need a JHA before you start. "
            "Talk to your supervisor.",
        ),
    )


def test_example_25_an_after_rating_of_10_is_good_to_go() -> None:
    """V3 uses the after rating, and 10 is below the threshold."""
    result: Verdict = verdict(
        _take5(before=("Possible", "Major"), after=("Rare", "Major")),
    )

    assert result == Verdict(can_start=True, reasons=())


def test_every_missing_control_reason_comes_before_the_jha_reason() -> None:
    """Every reason that applies is shown, V2 before V3."""
    take5 = Take5(
        template=BOOKLET_TEMPLATE,
        hazards=tuple(
            Hazard(
                description=name,
                before=rate(BOOKLET_MATRIX, "Likely", "Minor"),
                controls=(),
                after=rate(BOOKLET_MATRIX, "Likely", "Minor"),
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
