"""The Take 5 booklet's card.

For now a template holds its name and risk matrix. Task 0005 adds its questions.
"""

from typing import ClassVar

from pydantic import BaseModel, ConfigDict

from risk_assessment.domain.risk import RiskCell, RiskMatrix


class Take5Template(BaseModel):
    """The card a Take 5 is rated on, kept with the worker's assessment."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    name: str
    matrix: RiskMatrix


_BOOKLET_LIKELIHOODS: tuple[str, ...] = (
    "Almost Certain",
    "Likely",
    "Possible",
    "Unlikely",
    "Rare",
)
_BOOKLET_CONSEQUENCES: tuple[str, ...] = (
    "Low",
    "Minor",
    "Moderate",
    "Major",
    "Critical",
)

# The score of each cell, one row per likelihood above. Unlikely / Critical is 19, not
# the 18 printed on the card; see docs/decisions.md.
_BOOKLET_SCORES: tuple[tuple[int, ...], ...] = (
    (11, 16, 20, 23, 25),
    (7, 12, 17, 21, 24),
    (4, 8, 13, 18, 22),
    (2, 5, 9, 14, 19),
    (1, 3, 6, 10, 15),
)

# Each band's name with its lowest and highest score (spec R2).
_BOOKLET_BANDS: tuple[tuple[str, int, int], ...] = (
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

BOOKLET_TEMPLATE = Take5Template(name="Take 5 booklet", matrix=BOOKLET_MATRIX)
