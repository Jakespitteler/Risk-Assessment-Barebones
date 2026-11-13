"""Tests for rating a hazard, named by the spec's worked example numbers."""

import pytest

from risk_assessment.domain.risk import RiskCell, RiskMatrix, RiskRating, rate
from risk_assessment.domain.take5.template import BOOKLET_MATRIX


def test_example_1_rare_low_is_1_low_with_no_jha() -> None:
    """Worked example 1: the lowest cell of the booklet's matrix."""
    rating = rate(BOOKLET_MATRIX, "Rare", "Low")

    assert rating == RiskRating(
        likelihood="Rare", consequence="Low", score=1, band="Low"
    )
    assert not BOOKLET_MATRIX.needs_jha(rating.score)


def test_a_level_that_is_not_on_the_matrix_is_refused() -> None:
    """A likelihood the matrix doesn't have is an error, not a guess."""
    with pytest.raises(ValueError, match="'Sometimes' is not a likelihood"):
        rate(BOOKLET_MATRIX, "Sometimes", "Low")


def test_a_matrix_with_a_missing_cell_is_refused() -> None:
    """Every likelihood and consequence pair must have a cell."""
    with pytest.raises(ValueError, match="one cell per consequence"):
        RiskMatrix(
            likelihoods=("Likely", "Rare"),
            consequences=("Low", "High"),
            cells=((RiskCell(score=3, band="Medium"),), ()),
            jha_threshold=3,
        )
