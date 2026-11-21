"""A checked paper card saved as written, gaps and all (spec P1 to P5, task 0033).

A paper card skips the rules a worker meets while filling in the app (F2, T2 to T5,
R6, K2, C6): it is kept exactly as the person checking it confirmed it. Only what no
card can hold is refused: a level that isn't on the card's matrix, or a date or time
zone that can't be read.
"""

import re
from datetime import date, datetime, time
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from risk_assessment.domain.controls import Control
from risk_assessment.domain.risk import RiskMatrix, RiskRating, rate
from risk_assessment.domain.take5.draft import HazardDraft, RatingChoice, Take5Draft
from risk_assessment.domain.take5.saved import SavedTake5
from risk_assessment.domain.take5.take5 import Hazard, Take5
from risk_assessment.domain.take5.template import Take5Template
from risk_assessment.domain.take5.verdict import verdict

# The card's date as the page sends it: a date, or a date and a time to the minute.
_CARD_DATE: re.Pattern[str] = re.compile(r"\d{4}-\d{2}-\d{2}(T\d{2}:\d{2})?")
_EARLIEST_YEAR: int = 2000
_LATEST_YEAR: int = 2100

BAD_LEVEL_MESSAGE: str = "Pick a level from the card."
BAD_DATE_MESSAGE: str = "Give the card's date as it is written."
BAD_ZONE_MESSAGE: str = "This time zone isn't known."


class PaperCardError(ValueError):
    """A paper card holds something no card can: the message says what, and where.

    Attributes:
        path: The field's dotted path, such as "hazards.0.before.likelihood".
    """

    def __init__(self, path: str, message: str) -> None:
        """Say what is wrong, and where.

        Args:
            path: The field's dotted path.
            message: What a person should do about it.
        """
        super().__init__(message)
        self.path: str = path


def paper_started_at(filled_in_at: str | None, time_zone: str) -> datetime | None:
    """Turn the date written on a card into when it was started (P5).

    Args:
        filled_in_at: The card's date, "YYYY-MM-DD" or "YYYY-MM-DDTHH:MM", as read and
            checked, or None when the card has none.
        time_zone: The checker's time zone, such as "Australia/Perth".

    Returns:
        That moment in the checker's time zone, a date alone being the start of that
        day there, or None when the card has no date, so the scan time stands in.

    Raises:
        PaperCardError: If the date or the time zone can't be read.
    """
    try:
        zone = ZoneInfo(time_zone)
    except (ZoneInfoNotFoundError, ValueError) as error:
        raise PaperCardError("time_zone", BAD_ZONE_MESSAGE) from error
    if filled_in_at is None or not filled_in_at.strip():
        return None
    text: str = filled_in_at.strip()
    if not _CARD_DATE.fullmatch(text):
        raise PaperCardError("filled_in_at", BAD_DATE_MESSAGE)
    try:
        started_at: datetime = (
            datetime.fromisoformat(text).replace(tzinfo=zone)
            if "T" in text
            else datetime.combine(date.fromisoformat(text), time(), tzinfo=zone)
        )
    except ValueError as error:
        raise PaperCardError("filled_in_at", BAD_DATE_MESSAGE) from error
    if not _EARLIEST_YEAR <= started_at.year <= _LATEST_YEAR:
        raise PaperCardError("filled_in_at", BAD_DATE_MESSAGE)
    return started_at


def paper_take5(draft: Take5Draft, template: Take5Template) -> Take5:
    """Keep a checked paper card as written (P1, P2).

    A rating with only one half picked can't be scored, so it is kept as blank, as
    is an after rating on a hazard with no controls when none was written.

    Args:
        draft: The card as the person checked it.
        template: The card it is on.

    Returns:
        The card as a paper Take 5.

    Raises:
        PaperCardError: If a level isn't on the card's matrix.
    """
    return Take5(
        template=template,
        answers=dict(draft.answers),
        hazards=tuple(
            _hazard(hazard, template.matrix, f"hazards.{index}")
            for index, hazard in enumerate(draft.hazards)
        ),
        from_paper=True,
    )


def saved_paper_take5(  # noqa: PLR0913 - each is one part of the saved card
    take5_id: UUID,
    draft: Take5Draft,
    filled_in_at: str | None,
    time_zone: str,
    template: Take5Template,
    now: datetime,
) -> SavedTake5:
    """Build the saved Take 5 for a checked paper card: finished, with no question.

    Args:
        take5_id: The ID the page made for this card.
        draft: The card as the person checked it.
        filled_in_at: The card's date, as read and checked, or None.
        time_zone: The checker's time zone.
        template: The card it is on.
        now: When it is saved.

    Returns:
        The paper Take 5, finished now with its verdict (P1, P3).

    Raises:
        PaperCardError: If a level, the date or the time zone can't be used.
    """
    take5: Take5 = paper_take5(draft, template)
    return SavedTake5(
        template=template,
        answers=take5.answers,
        hazards=take5.hazards,
        from_paper=True,
        id=take5_id,
        created_at=now,
        worker_name=draft.worker_name.strip(),
        job=draft.job.strip(),
        location=draft.location.strip(),
        finished_at=now,
        verdict=verdict(take5),
        started_at=paper_started_at(filled_in_at, time_zone),
    )


def _hazard(draft: HazardDraft, matrix: RiskMatrix, path: str) -> Hazard:
    """Keep one hazard as written.

    Args:
        draft: The hazard as checked.
        matrix: The card's matrix.
        path: Where it is, such as "hazards.0".

    Returns:
        The hazard, with any blank rating or kind kept blank.
    """
    return Hazard(
        description=draft.description.strip(),
        before=_rating(draft.before, matrix, f"{path}.before"),
        controls=tuple(
            Control(description=control.description.strip(), kind=control.kind)
            for control in draft.controls
        ),
        after=_rating(draft.after, matrix, f"{path}.after"),
    )


def _rating(choice: RatingChoice, matrix: RiskMatrix, path: str) -> RiskRating | None:
    """Look up a rating, keeping it blank when either half is.

    Args:
        choice: The likelihood and consequence as checked.
        matrix: The card's matrix.
        path: Where the rating is, such as "hazards.0.before".

    Returns:
        The rating, or None when either half is blank.

    Raises:
        PaperCardError: If a level isn't on the matrix.
    """
    if choice.likelihood is not None and choice.likelihood not in matrix.likelihoods:
        raise PaperCardError(f"{path}.likelihood", BAD_LEVEL_MESSAGE)
    if choice.consequence is not None and choice.consequence not in matrix.consequences:
        raise PaperCardError(f"{path}.consequence", BAD_LEVEL_MESSAGE)
    if choice.likelihood is None or choice.consequence is None:
        return None
    return rate(matrix, choice.likelihood, choice.consequence)
