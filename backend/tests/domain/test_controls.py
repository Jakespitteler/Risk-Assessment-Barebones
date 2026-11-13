"""The six control kinds and strengths specified by the booklet."""

import pytest

from risk_assessment.domain.controls import ControlKind


@pytest.mark.parametrize(
    ("kind", "is_strong"),
    [
        (ControlKind.REMOVE, True),
        (ControlKind.ISOLATE, True),
        (ControlKind.BARRICADE, True),
        (ControlKind.SYSTEMS, False),
        (ControlKind.BEHAVIOUR, False),
        (ControlKind.PPE, False),
    ],
)
def test_control_strength_matches_the_card(kind: ControlKind, is_strong: bool) -> None:
    """Only removing, isolating and barricading count as strong controls."""
    assert kind.is_strong is is_strong
