"""The Take 5 booklet's card.

For now this is only the booklet's risk matrix. Its questions, and the `Take5Template`
that holds them with the matrix, come in tasks 0003 and 0005.
"""

from risk_assessment.domain.risk import RiskCell, RiskMatrix

_BOOKLET_LIKELIHOODS = ("Almost Certain", "Likely", "Possible", "Unlikely", "Rare")
_BOOKLET_CONSEQUENCES = ("Low", "Minor", "Moderate", "Major", "Critical")

# The score of each cell, one row per likelihood above. Unlikely / Critical is 19, not
# the 18 printed on the card; see docs/decisions.md.
_BOOKLET_SCORES = (
    (11, 16, 20, 23, 25),
    (7, 12, 17, 21, 24),
    (4, 8, 13, 18, 22),
    (2, 5, 9, 14, 19),
    (1, 3, 6, 10, 15),
)

# Each band's name with its lowest and highest score (spec R2).
_BOOKLET_BANDS = (
    ("Low", 1, 5),
    ("Moderate", 6, 9),
    ("High", 10, 17),
    ("Extreme", 18, 25),
)


def _booklet_band(score: int) -> str:
    """Name the booklet band that a score falls in."""
    return next(
        name for name, lowest, highest in _BOOKLET_BANDS if lowest <= score <= highest
    )


BOOKLET_MATRIX = RiskMatrix(
    likelihoods=_BOOKLET_LIKELIHOODS,
    consequences=_BOOKLET_CONSEQUENCES,
    cells=tuple(
        tuple(RiskCell(score=score, band=_booklet_band(score)) for score in row)
        for row in _BOOKLET_SCORES
    ),
    jha_threshold=11,
)
