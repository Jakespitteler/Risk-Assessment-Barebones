"""Group saved Take 5s by where the job is, hottest area first (spec A1 to A5).

An area is where the job is, as the worker typed it (A1). An area is hot when many of
its Take 5s had a hazard that needed a Job Hazard Analysis before controls (A3). It
needs no AI: every number here can be checked by hand (decision D113).
"""

import re
from collections import Counter
from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import ClassVar

from pydantic import BaseModel, ConfigDict

from risk_assessment.domain.questions import Answer, QuestionRole
from risk_assessment.domain.take5.ranking import highest_risk, thought_gaps
from risk_assessment.domain.take5.saved import SavedTake5
from risk_assessment.domain.take5.take5 import Hazard

# How far back the page looks, today included (A2, decision D112).
AREA_DAYS: int = 30
# How many of an area's most common Yes answers it shows (A5).
COMMON_YES_COUNT: int = 3

_NOT_A_LETTER_OR_DIGIT: re.Pattern[str] = re.compile(r"[\W_]+")


class CommonYes(BaseModel):
    """A hazard question answered Yes in an area, and how many times.

    Attributes:
        question: The card's question, word for word.
        count: How many of the area's Take 5s answered it Yes.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    question: str
    count: int


class AreaRisk(BaseModel):
    """What the Take 5s in one area show (A3 to A5).

    Attributes:
        name: The area, as it was typed most often (A1).
        take5_count: How many Take 5s were done there.
        high_risk_count: How many had a hazard that needed a JHA before controls (A3).
        dont_start_count: How many got "Don't start yet". An unfinished one has no
            verdict yet, so it isn't counted.
        thought_gap_count: How many thought gaps they had between them (W2 to W5, W10).
        highest_score: The highest before-controls score of any hazard there.
        highest_band: That score's band, such as "Extreme".
        common_yes: Up to 3 hazard questions answered Yes most often there (A5).
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    name: str
    take5_count: int
    high_risk_count: int
    dont_start_count: int
    thought_gap_count: int
    highest_score: int
    highest_band: str
    common_yes: tuple[CommonYes, ...]


def area_key(location: str) -> str:
    """Write where a job is so that spellings of the same place match (A1).

    Capitals, spaces and punctuation are ignored, so "Light vehicle workshop" and
    "light-vehicle  workshop." are the same area.

    Args:
        location: Where the job is, as the worker typed it.

    Returns:
        The words in lower case, one space apart. Empty when there are none.
    """
    return _NOT_A_LETTER_OR_DIGIT.sub(" ", location.casefold()).strip()


def area_since(midnight_today: datetime) -> datetime:
    """Find where the last 30 days, today included, start (A2).

    Args:
        midnight_today: Midnight today where the phone is, with its time zone.

    Returns:
        Midnight 29 days before it.
    """
    return midnight_today - timedelta(days=AREA_DAYS - 1)


def is_high_risk(take5: SavedTake5) -> bool:
    """Say whether a Take 5 had a hazard that needed a JHA before controls (A3, R3).

    Each Take 5 is judged on its own card's threshold: 11 or more on the booklet.

    Args:
        take5: A saved Take 5.

    Returns:
        True when its highest before-controls score needs a JHA.
    """
    return take5.template.matrix.needs_jha(highest_risk(take5).before.score)


def risk_by_area(take5s: Sequence[SavedTake5]) -> tuple[AreaRisk, ...]:
    """Group Take 5s by area, hottest first (A1, A4).

    A Take 5 with no location is left out: it can't be placed.

    Args:
        take5s: The Take 5s to group, in any order.

    Returns:
        One entry per area: the most high-risk Take 5s first, then the most "Don't
        start yet", then the most thought gaps, then the most Take 5s, then by name.
    """
    by_area: dict[str, list[SavedTake5]] = {}
    for take5 in sorted(take5s, key=lambda each: each.created_at, reverse=True):
        key: str = area_key(take5.location)
        if key:
            by_area.setdefault(key, []).append(take5)
    areas: list[AreaRisk] = [_area(newest_first) for newest_first in by_area.values()]
    return tuple(
        sorted(
            areas,
            key=lambda area: (
                -area.high_risk_count,
                -area.dont_start_count,
                -area.thought_gap_count,
                -area.take5_count,
                area.name.casefold(),
            ),
        ),
    )


def _area(newest_first: Sequence[SavedTake5]) -> AreaRisk:
    """Work out what one area's Take 5s show (A3 to A5).

    Args:
        newest_first: The area's Take 5s, the newest first.

    Returns:
        The area's counts, its highest risk and its most common Yes answers.
    """
    riskiest: Hazard = max(
        (highest_risk(take5) for take5 in newest_first),
        key=lambda hazard: hazard.before.score,
    )
    return AreaRisk(
        name=_most_typed(newest_first),
        take5_count=len(newest_first),
        high_risk_count=sum(is_high_risk(take5) for take5 in newest_first),
        dont_start_count=sum(
            take5.verdict is not None and not take5.verdict.can_start
            for take5 in newest_first
        ),
        thought_gap_count=sum(len(thought_gaps(take5)) for take5 in newest_first),
        highest_score=riskiest.before.score,
        highest_band=riskiest.before.band,
        common_yes=_common_yes(newest_first),
    )


def _most_typed(newest_first: Sequence[SavedTake5]) -> str:
    """Pick the spelling of an area typed most often, the newest on a tie (A1).

    Args:
        newest_first: The area's Take 5s, the newest first.

    Returns:
        That spelling, with spaces at the ends taken off.
    """
    # `Counter` keeps the order each spelling was first seen, the newest first, and
    # `most_common` keeps that order among equal counts.
    spellings: Counter[str] = Counter(take5.location.strip() for take5 in newest_first)
    return spellings.most_common(1)[0][0]


def _common_yes(newest_first: Sequence[SavedTake5]) -> tuple[CommonYes, ...]:
    """Find the hazard questions answered Yes most often in an area (A5).

    Args:
        newest_first: The area's Take 5s, the newest first.

    Returns:
        Up to 3, the most often first, and in the card's order on a tie.
    """
    counts: Counter[str] = Counter()
    card_order: dict[str, int] = {}
    for take5 in newest_first:
        for place, question in enumerate(take5.template.questions):
            if (
                question.role is QuestionRole.HAZARD
                and take5.answers.get(question.id) is Answer.YES
            ):
                counts[question.text] += 1
                card_order.setdefault(question.text, place)
    ordered: list[tuple[str, int]] = sorted(
        counts.items(),
        key=lambda each: (-each[1], card_order[each[0]]),
    )
    return tuple(
        CommonYes(question=question, count=count)
        for question, count in ordered[:COMMON_YES_COUNT]
    )
