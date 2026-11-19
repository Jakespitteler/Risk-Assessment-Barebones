"""Tests for rating a hazard, named by the spec's worked example numbers."""

import pytest

from risk_assessment.domain.risk import RiskCell, RiskMatrix, RiskRating, rate
from risk_assessment.domain.take5.template import BOOKLET_MATRIX


def test_example_1_rare_low_is_1_low_with_no_jha() -> None:
    """Worked example 1: the lowest cell of the booklet's matrix (R1, R2, R3)."""
    rating: RiskRating = rate(BOOKLET_MATRIX, "Rare", "Low")

    assert rating == RiskRating(
        likelihood="Rare",
        consequence="Low",
        score=1,
        band="Low",
    )
    assert not BOOKLET_MATRIX.needs_jha(rating.score)


@pytest.mark.parametrize(
    ("likelihood", "consequence", "score", "band", "needs_jha"),
    [
        pytest.param(
            "Almost Certain",
            "Critical",
            25,
            "Extreme",
            True,
            id="test_example_2",
        ),
        pytest.param("Unlikely", "Minor", 5, "Low", False, id="test_example_3"),
        pytest.param("Rare", "Moderate", 6, "Moderate", False, id="test_example_4"),
        pytest.param("Unlikely", "Moderate", 9, "Moderate", False, id="test_example_5"),
        pytest.param("Rare", "Major", 10, "High", False, id="test_example_6"),
        pytest.param("Almost Certain", "Low", 11, "High", True, id="test_example_7"),
        pytest.param("Likely", "Moderate", 17, "High", True, id="test_example_8"),
        pytest.param("Possible", "Major", 18, "Extreme", True, id="test_example_9"),
        pytest.param("Unlikely", "Critical", 19, "Extreme", True, id="test_example_10"),
    ],
)
def test_example_2_to_10_rating_boundaries(
    likelihood: str,
    consequence: str,
    score: int,
    band: str,
    needs_jha: bool,
) -> None:
    """Each numbered example checks its score, band and JHA decision (R1, R2, R3)."""
    rating: RiskRating = rate(BOOKLET_MATRIX, likelihood, consequence)
    assert rating == RiskRating(
        likelihood=likelihood,
        consequence=consequence,
        score=score,
        band=band,
    )
    assert BOOKLET_MATRIX.needs_jha(rating.score) is needs_jha


@pytest.mark.parametrize(
    ("likelihood", "expected"),
    [
        (
            "Almost Certain",
            (
                (11, "High"),
                (16, "High"),
                (20, "Extreme"),
                (23, "Extreme"),
                (25, "Extreme"),
            ),
        ),
        (
            "Likely",
            (
                (7, "Moderate"),
                (12, "High"),
                (17, "High"),
                (21, "Extreme"),
                (24, "Extreme"),
            ),
        ),
        (
            "Possible",
            (
                (4, "Low"),
                (8, "Moderate"),
                (13, "High"),
                (18, "Extreme"),
                (22, "Extreme"),
            ),
        ),
        (
            "Unlikely",
            ((2, "Low"), (5, "Low"), (9, "Moderate"), (14, "High"), (19, "Extreme")),
        ),
        ("Rare", ((1, "Low"), (3, "Low"), (6, "Moderate"), (10, "High"), (15, "High"))),
    ],
)
def test_all_25_booklet_cells_match_the_spec(
    likelihood: str,
    expected: tuple[tuple[int, str], ...],
) -> None:
    """Check all printed cells against independent expected scores and bands (R1)."""
    consequences: tuple[str, ...] = ("Low", "Minor", "Moderate", "Major", "Critical")
    for consequence, (score, band) in zip(consequences, expected, strict=True):
        assert rate(BOOKLET_MATRIX, likelihood, consequence) == RiskRating(
            likelihood=likelihood,
            consequence=consequence,
            score=score,
            band=band,
        )


def test_a_score_on_the_threshold_needs_a_jha() -> None:
    """The JHA threshold comes from the matrix, and a score equal to it needs a JHA."""
    matrix = RiskMatrix(
        likelihoods=("Likely",),
        consequences=("Bad",),
        cells=((RiskCell(score=7, band="Serious"),),),
        jha_threshold=7,
    )

    assert matrix.needs_jha(rate(matrix, "Likely", "Bad").score)


def test_a_level_that_is_not_on_the_matrix_is_refused() -> None:
    """A likelihood the matrix doesn't have is an error, not a guess."""
    with pytest.raises(ValueError, match="'Sometimes' is not a likelihood"):
        rate(BOOKLET_MATRIX, "Sometimes", "Low")

    with pytest.raises(ValueError, match="'Harmless' is not a consequence"):
        rate(BOOKLET_MATRIX, "Rare", "Harmless")


def test_a_matrix_with_a_missing_cell_is_refused() -> None:
    """Every likelihood and consequence pair must have a cell."""
    with pytest.raises(ValueError, match="one cell per consequence"):
        RiskMatrix(
            likelihoods=("Likely", "Rare"),
            consequences=("Low", "High"),
            cells=((RiskCell(score=3, band="Medium"),), ()),
            jha_threshold=3,
        )
