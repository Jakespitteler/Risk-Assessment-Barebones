"""The risk matrix, and how a hazard is rated on it (spec rules R1 to R3).

Nothing here knows about a Take 5 or about any one company's card. A matrix is data
that is handed to `rate()`, so another company's matrix needs no new code.
"""

from typing import ClassVar, Self

from pydantic import BaseModel, ConfigDict, model_validator


class RiskCell(BaseModel):
    """One square of a risk matrix: the score it gives and the band that score is in."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    score: int
    band: str


class RiskMatrix(BaseModel):
    """A risk matrix as data.

    Attributes:
        likelihoods: The likelihood scale, most likely first, as printed down the side
            of the card.
        consequences: The consequence scale, least severe first, as printed across the
            top.
        cells: One row per likelihood and, in each row, one cell per consequence, in
            the order of the scales.
        jha_threshold: The lowest score that needs a Job Hazard Analysis (spec R3).
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    likelihoods: tuple[str, ...]
    consequences: tuple[str, ...]
    cells: tuple[tuple[RiskCell, ...], ...]
    jha_threshold: int

    @model_validator(mode="after")
    def _has_one_cell_per_pair(self) -> Self:
        """Refuse a matrix whose grid of cells doesn't match its two scales."""
        rows_match: bool = len(self.cells) == len(self.likelihoods)
        columns_match: bool = all(
            len(row) == len(self.consequences) for row in self.cells
        )
        if not (rows_match and columns_match):
            raise ValueError(
                "A risk matrix needs one row per likelihood"
                " and one cell per consequence."
            )
        return self

    def needs_jha(self, score: int) -> bool:
        """Say whether a score needs a Job Hazard Analysis (spec R3)."""
        return score >= self.jha_threshold


class RiskRating(BaseModel):
    """A likelihood and consequence, with the score and band the matrix gives them.

    The score and band are always looked up, never typed in, so only `rate()` should
    make one.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    likelihood: str
    consequence: str
    score: int
    band: str


def rate(matrix: RiskMatrix, likelihood: str, consequence: str) -> RiskRating:
    """Rate a hazard by looking up its likelihood and consequence (spec R1).

    Args:
        matrix: The matrix the hazard is rated on.
        likelihood: One of the matrix's likelihoods, such as "Rare".
        consequence: One of the matrix's consequences, such as "Low".

    Returns:
        The rating, with the score and band of that cell.

    Raises:
        ValueError: If the likelihood or the consequence is not on the matrix's scale.
    """
    row: int = _position_on_scale(matrix.likelihoods, likelihood, "likelihood")
    column: int = _position_on_scale(matrix.consequences, consequence, "consequence")
    cell: RiskCell = matrix.cells[row][column]
    return RiskRating(
        likelihood=likelihood, consequence=consequence, score=cell.score, band=cell.band
    )


def _position_on_scale(scale: tuple[str, ...], level: str, scale_name: str) -> int:
    """Find where a level sits on a scale, with a clear error when it isn't there."""
    if level not in scale:
        raise ValueError(f"'{level}' is not a {scale_name} on this matrix.")
    return scale.index(level)
