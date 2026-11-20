"""Rank saved Take 5s worst first, each with one line saying why (spec W1 to W7).

"Worst" weighs how risky the job is against how little thought the answers show
(decision D91). The fixed rules here score every Take 5 and need no AI. An AI may then
reorder the worst few and write their lines; this module also writes what the AI is
given and checks what it sends back, so a bad reply never reaches the page.
"""

import json
from collections.abc import Sequence
from datetime import timedelta
from enum import StrEnum
from typing import ClassVar

from pydantic import BaseModel, ConfigDict

from risk_assessment.domain.take5.challenge import challenge_text
from risk_assessment.domain.take5.saved import SavedTake5
from risk_assessment.domain.take5.take5 import Hazard
from risk_assessment.domain.wording import word_count

# A hazard or an answer shorter than this shows little thought (W2, W4). It matches
# the booklet's word minimum for a hazard linked to a Yes (T6).
THOUGHTFUL_WORDS: int = 6
# A Take 5 submitted this soon after it was started was rushed (W5).
RUSHED_UNDER: timedelta = timedelta(minutes=2)
# Each sign of little thought adds this to the score (W1).
GAP_POINTS: int = 5
# How many of the worst the AI reorders and writes lines for (W6).
AI_RANKED_COUNT: int = 10
AI_RANKING_TIME_LIMIT_SECONDS: float = 20
# The longest line the page will show from an AI (W6).
LINE_MAX_CHARACTERS: int = 200


class RankedBy(StrEnum):
    """Who placed a Take 5 and wrote its line."""

    AI = "ai"
    RULES = "rules"


class RankedTake5(BaseModel):
    """One Take 5's place in a ranking.

    Attributes:
        take5: The saved Take 5.
        score: Its score from the fixed rules (W1), highest first.
        line: One line saying why it sits where it does.
        ranked_by: Whether the AI or the fixed rules placed it and wrote the line.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    take5: SavedTake5
    score: int
    line: str
    ranked_by: RankedBy


def highest_risk(take5: SavedTake5) -> Hazard:
    """Find the hazard with the highest rating before controls (W1).

    Args:
        take5: A saved Take 5, which always has at least one hazard.

    Returns:
        The first hazard with the highest before score.
    """
    return max(take5.hazards, key=lambda hazard: hazard.before.score)


def thought_gaps(take5: SavedTake5) -> tuple[str, ...]:
    """List each sign that the answers show little thought, in plain words (W2 to W5).

    Args:
        take5: A saved Take 5.

    Returns:
        One phrase per sign found, such as "Question not answered". Each hazard
        counts on its own, so two short hazards give two phrases.
    """
    gaps: list[str] = []
    for hazard in take5.hazards:
        if word_count(hazard.description) < THOUGHTFUL_WORDS:
            gaps.append(f"“{hazard.description}” is under {THOUGHTFUL_WORDS} words")
    for hazard in take5.hazards:
        if hazard.controls and hazard.after.score == hazard.before.score:
            gaps.append(f"the controls for “{hazard.description}” don't lower its risk")
    answer: str | None = take5.challenge.answer if take5.challenge else None
    if not take5.is_finished:
        gaps.append("the question was never answered")
    elif answer is not None and word_count(answer) < THOUGHTFUL_WORDS:
        gaps.append(f"the answer to the question is under {THOUGHTFUL_WORDS} words")
    if (
        take5.started_at is not None
        and take5.created_at - take5.started_at < RUSHED_UNDER
    ):
        gaps.append("it was filled in in under 2 minutes")
    return tuple(gaps)


def worst_score(take5: SavedTake5) -> int:
    """Score how bad a Take 5 is: its highest risk plus points for little thought (W1).

    Args:
        take5: A saved Take 5.

    Returns:
        The highest before-controls score, plus `GAP_POINTS` for each thought gap.
    """
    return highest_risk(take5).before.score + GAP_POINTS * len(thought_gaps(take5))


def rule_line(take5: SavedTake5) -> str:
    """Write the line the fixed rules give a Take 5 (W1).

    Args:
        take5: A saved Take 5.

    Returns:
        Such as "Highest risk 18 Extreme. The question was never answered."
    """
    riskiest: Hazard = highest_risk(take5)
    risk: str = f"Highest risk {riskiest.before.score} {riskiest.before.band}."
    gaps: str = "; ".join(thought_gaps(take5))
    if not gaps:
        return f"{risk} No signs of a rushed Take 5."
    return f"{risk} {gaps[0].upper()}{gaps[1:]}."


def rank_by_rules(take5s: Sequence[SavedTake5]) -> tuple[RankedTake5, ...]:
    """Rank Take 5s by the fixed rules alone: highest score first (W1).

    Args:
        take5s: The Take 5s to rank, in any order.

    Returns:
        Each Take 5 with its score and rule line, highest score first, and the newest
        first among equal scores.
    """
    newest_first: list[SavedTake5] = sorted(
        take5s,
        key=lambda take5: take5.created_at,
        reverse=True,
    )
    ranked: list[RankedTake5] = [
        RankedTake5(
            take5=take5,
            score=worst_score(take5),
            line=rule_line(take5),
            ranked_by=RankedBy.RULES,
        )
        for take5 in newest_first
    ]
    return tuple(sorted(ranked, key=lambda each: each.score, reverse=True))


def ranking_text(worst: Sequence[RankedTake5]) -> str:
    """Write out what the AI is given about the worst Take 5s (W6).

    Each is numbered from 1 in the fixed rules' order. Each has what the challenge
    question is given (spec C1), plus the question it was asked, the answer, and the
    minutes it took. The worker's name is never included.

    Args:
        worst: The worst Take 5s by the fixed rules.

    Returns:
        JSON, so everything a worker typed sits inside a quoted value.
    """
    described: list[dict[str, object]] = []
    for number, ranked in enumerate(worst, start=1):
        take5: SavedTake5 = ranked.take5
        entry: dict[str, object] = {"number": number}
        entry.update(json.loads(challenge_text(take5, take5.job, take5.location)))
        entry["question_asked"] = take5.challenge.question if take5.challenge else None
        entry["answer"] = take5.challenge.answer if take5.challenge else None
        entry["minutes_taken"] = (
            round((take5.created_at - take5.started_at).total_seconds() / 60)
            if take5.started_at is not None
            else None
        )
        described.append(entry)
    return json.dumps({"take5s": described}, indent=2, ensure_ascii=False)


class _AiPlace(BaseModel):
    """One place in the AI's reply, before it is checked."""

    number: int
    why: str


class _AiReply(BaseModel):
    """The AI's whole reply, before it is checked."""

    ranking: list[_AiPlace]


def checked_ai_order(reply: str, count: int) -> tuple[tuple[int, str], ...] | None:
    """Keep the AI's order and lines only if every one passes W6.

    Args:
        reply: The AI's reply, exactly as it came.
        count: How many Take 5s it was given, numbered 1 to `count`.

    Returns:
        Each number, from 1, with its line, worst first; or None when the reply isn't
        the expected JSON, doesn't hold each number exactly once, or has a line that
        is empty, over `LINE_MAX_CHARACTERS` or more than one line.
    """
    try:
        parsed: _AiReply = _AiReply.model_validate_json(reply.strip())
    except ValueError:
        return None
    numbers: list[int] = [place.number for place in parsed.ranking]
    if sorted(numbers) != list(range(1, count + 1)):
        return None
    order: list[tuple[int, str]] = []
    for place in parsed.ranking:
        line: str = place.why.strip()
        if not line or len(line) > LINE_MAX_CHARACTERS or "\n" in line:
            return None
        order.append((place.number, line))
    return tuple(order)


def with_ai_order(
    ranked: Sequence[RankedTake5],
    ai_order: Sequence[tuple[int, str]],
) -> tuple[RankedTake5, ...]:
    """Put the worst few in the AI's order with its lines; the rest stay as they were.

    A line that names the worker is replaced by the rule line, in case a name typed
    into a job or hazard reached the AI and came back (W6).

    Args:
        ranked: The whole ranking by the fixed rules.
        ai_order: Each number, from 1, with its line, worst first, as
            `checked_ai_order()` returns it for the first `len(ai_order)` Take 5s.

    Returns:
        The AI's order for the Take 5s it was given, then the rest by the rules.
    """
    reordered: list[RankedTake5] = []
    for number, line in ai_order:
        place: RankedTake5 = ranked[number - 1]
        names_worker: bool = (
            place.take5.worker_name.casefold().strip() in line.casefold()
        )
        reordered.append(
            place
            if names_worker
            else place.model_copy(update={"line": line, "ranked_by": RankedBy.AI}),
        )
    return (*reordered, *ranked[len(ai_order) :])
