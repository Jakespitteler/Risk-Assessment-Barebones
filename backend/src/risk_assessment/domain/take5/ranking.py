"""Rank saved Take 5s worst first, and find the best, each with a line (W1 to W9).

"Worst" weighs how risky the job is against how little thought the answers show
(decision D91). The fixed rules here score every Take 5 and need no AI. An AI may then
reorder the worst few and write their lines; this module also writes what the AI is
given and checks what it sends back, so a bad reply never reaches the page.
"""

import json
import math
import re
import statistics
from collections.abc import Sequence
from datetime import timedelta
from enum import StrEnum
from typing import ClassVar

from pydantic import BaseModel, ConfigDict

from risk_assessment.domain.risk import RiskRating
from risk_assessment.domain.take5.challenge import challenge_text
from risk_assessment.domain.take5.saved import SavedTake5
from risk_assessment.domain.take5.take5 import HazardFlag
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
# How many careful Take 5s the AI chooses the best from (W8).
BEST_SHORTLIST_COUNT: int = 5
RUSHED_GAP: str = "it was filled in in under 2 minutes"
# What a hazard kept after the hazard check flagged it says about it (W10).
_KEPT: dict[HazardFlag, str] = {
    HazardFlag.VAGUE: "was kept after the check asked for more",
    HazardFlag.STOCK: "was kept though it could fit any job",
    HazardFlag.UNFIT: "was kept though it doesn't seem to fit the job",
}


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


def highest_risk(take5: SavedTake5) -> RiskRating | None:
    """Find the highest rating before controls (W1).

    Args:
        take5: A saved Take 5.

    Returns:
        The first highest before rating, or None for a paper card with no hazard
        rated before controls (P4).
    """
    ratings: list[RiskRating] = [
        hazard.before for hazard in take5.hazards if hazard.before is not None
    ]
    return max(ratings, key=lambda rating: rating.score, default=None)


def highest_score(take5: SavedTake5) -> int:
    """Give the highest before-controls score, or 0 when nothing was rated (W1, P4).

    Args:
        take5: A saved Take 5.

    Returns:
        The score.
    """
    riskiest: RiskRating | None = highest_risk(take5)
    return riskiest.score if riskiest is not None else 0


def _highest_risk_words(take5: SavedTake5) -> str:
    """Say a Take 5's highest risk, such as "Highest risk 18 Extreme".

    Args:
        take5: A saved Take 5.

    Returns:
        The words, or "No risk rated" for a paper card with no rating (P4).
    """
    riskiest: RiskRating | None = highest_risk(take5)
    if riskiest is None:
        return "No risk rated"
    return f"Highest risk {riskiest.score} {riskiest.band}"


def thought_gaps(take5: SavedTake5) -> tuple[str, ...]:
    """List each sign the answers show little thought, in plain words (W2 to W5, W10).

    Args:
        take5: A saved Take 5.

    Returns:
        One phrase per sign found, such as "Question not answered". Each hazard
        counts on its own, so two short hazards give two phrases.
    """
    gaps: list[str] = list(paper_gaps(take5))
    for hazard in take5.hazards:
        if not hazard.description:
            gaps.append("a hazard has no description")
        elif word_count(hazard.description) < THOUGHTFUL_WORDS:
            gaps.append(f"“{hazard.description}” is under {THOUGHTFUL_WORDS} words")
    for hazard in take5.hazards:
        if (
            hazard.controls
            and hazard.before is not None
            and hazard.after is not None
            and hazard.after.score == hazard.before.score
        ):
            name: str = f"“{hazard.description}”" if hazard.description else "a hazard"
            gaps.append(f"the controls for {name} don't lower its risk")
    for hazard in take5.hazards:
        if (
            hazard.kept_flag is not None
            and word_count(hazard.description) >= THOUGHTFUL_WORDS
        ):
            gaps.append(f"“{hazard.description}” {_KEPT[hazard.kept_flag]}")
    answer: str | None = take5.challenge.answer if take5.challenge else None
    if not take5.is_finished:
        gaps.append("the question was never answered")
    elif answer is not None and word_count(answer) < THOUGHTFUL_WORDS:
        gaps.append(f"the answer to the question is under {THOUGHTFUL_WORDS} words")
    taken: timedelta | None = time_taken(take5)
    if taken is not None and taken < RUSHED_UNDER:
        gaps.append(RUSHED_GAP)
    return tuple(gaps)


def paper_gaps(take5: SavedTake5) -> tuple[str, ...]:
    """List each blank a paper card left, each one a thought gap (P4).

    Args:
        take5: A saved Take 5. Any other than a paper card has no blanks.

    Returns:
        One phrase per blank: a question with no answer, no hazard at all, a hazard
        with no rating before controls, and a control with no kind.
    """
    gaps: list[str] = [
        f"“{question.text}” has no answer"
        for question in take5.template.questions
        if question.id not in take5.answers
    ]
    if take5.from_paper and not take5.hazards:
        gaps.append("no hazard was written down")
    for hazard in take5.hazards:
        name: str = f"“{hazard.description}”" if hazard.description else "a hazard"
        if hazard.before is None:
            gaps.append(f"{name} has no rating")
        if any(control.kind is None for control in hazard.controls):
            gaps.append(f"a control for {name} has no kind")
    return tuple(gaps)


def time_taken(take5: SavedTake5) -> timedelta | None:
    """Find how long a Take 5 took, from its start to its save (W5).

    Args:
        take5: A saved Take 5.

    Returns:
        The time taken, or None when it has no start time, a start time after it
        was saved, as a phone whose clock is fast can send, or it is a paper card,
        whose time taken isn't known (P5).
    """
    if (
        take5.from_paper
        or take5.started_at is None
        or take5.started_at > take5.created_at
    ):
        return None
    return take5.created_at - take5.started_at


def worst_score(take5: SavedTake5) -> int:
    """Score how bad a Take 5 is: its highest risk plus points for little thought (W1).

    Args:
        take5: A saved Take 5.

    Returns:
        The highest before-controls score, plus `GAP_POINTS` for each thought gap.
    """
    return highest_score(take5) + GAP_POINTS * len(thought_gaps(take5))


def rule_line(take5: SavedTake5) -> str:
    """Write the line the fixed rules give a Take 5 (W1).

    Args:
        take5: A saved Take 5.

    Returns:
        Such as "Highest risk 18 Extreme. The question was never answered."
    """
    risk: str = f"{_highest_risk_words(take5)}."
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
    return json.dumps(
        {"take5s": _described([ranked.take5 for ranked in worst])},
        indent=2,
        ensure_ascii=False,
    )


def _described(take5s: Sequence[SavedTake5]) -> list[dict[str, object]]:
    """Describe Take 5s for the AI, numbered from 1, without any name (W6, W8).

    Args:
        take5s: The Take 5s, in the order they are numbered.

    Returns:
        For each, its number, what the challenge question is given (C1), the
        question asked, the answer and the minutes taken.
    """
    described: list[dict[str, object]] = []
    for number, take5 in enumerate(take5s, start=1):
        entry: dict[str, object] = {"number": number}
        entry.update(json.loads(challenge_text(take5, take5.job, take5.location)))
        entry["question_asked"] = take5.challenge.question if take5.challenge else None
        entry["answer"] = take5.challenge.answer if take5.challenge else None
        entry["minutes_taken"] = minutes_taken(take5)
        described.append(entry)
    return described


# A one-letter initial is too common a word to look for.
_SHORTEST_NAME_PART: int = 2


def _words(text: str) -> set[str]:
    """Split text into its words, in lower case, for matching a name.

    Args:
        text: Any text.

    Returns:
        Its words, without punctuation.
    """
    return {word.casefold() for word in re.findall(r"[^\W\d_]+", text)}


class _AiPlace(BaseModel):
    """One place in the AI's reply, before it is checked."""

    number: int
    why: str


class _AiReply(BaseModel):
    """The AI's whole reply, before it is checked."""

    ranking: list[_AiPlace]


def _without_fence(reply: str) -> str:
    """Take off the ```json fence a model sometimes puts round its JSON.

    Args:
        reply: The AI's reply.

    Returns:
        The reply without the fence, trimmed.
    """
    text: str = reply.strip()
    if text.startswith("```") and text.endswith("```"):
        text = text.removeprefix("```json").removeprefix("```").removesuffix("```")
    return text.strip()


def _is_one_good_line(line: str) -> bool:
    """Check an AI's line is one line, not empty and not too long (W6).

    Args:
        line: The line, trimmed.

    Returns:
        True when the page can show it.
    """
    return bool(line) and len(line) <= LINE_MAX_CHARACTERS and "\n" not in line


def _worker_names(take5s: Sequence[SavedTake5]) -> frozenset[str]:
    """Collect each word of the workers' names worth looking for in a line (W6).

    Args:
        take5s: The Take 5s the AI was given.

    Returns:
        Each word of two letters or more, in lower case.
    """
    return frozenset(
        part
        for take5 in take5s
        for part in _words(take5.worker_name)
        if len(part) >= _SHORTEST_NAME_PART
    )


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
        parsed: _AiReply = _AiReply.model_validate_json(_without_fence(reply))
    except ValueError:
        return None
    numbers: list[int] = [place.number for place in parsed.ranking]
    if sorted(numbers) != list(range(1, count + 1)):
        return None
    order: list[tuple[int, str]] = []
    for place in parsed.ranking:
        line: str = place.why.strip()
        if not _is_one_good_line(line):
            return None
        order.append((place.number, line))
    return tuple(order)


def with_ai_order(
    ranked: Sequence[RankedTake5],
    ai_order: Sequence[tuple[int, str]],
) -> tuple[RankedTake5, ...]:
    """Put the worst few in the AI's order with its lines; the rest stay as they were.

    A line holding any word of the name of a worker it was given is replaced by the
    rule line, in case a name typed into a job or hazard reached the AI and came back
    (W6). The AI's order still stands.

    Args:
        ranked: The whole ranking by the fixed rules.
        ai_order: Each number, from 1, with its line, worst first, as
            `checked_ai_order()` returns it for the first `len(ai_order)` Take 5s.

    Returns:
        The AI's order for the Take 5s it was given, then the rest by the rules.
    """
    names: frozenset[str] = _worker_names(
        [place.take5 for place in ranked[: len(ai_order)]],
    )
    reordered: list[RankedTake5] = []
    for number, line in ai_order:
        place: RankedTake5 = ranked[number - 1]
        names_a_worker: bool = not names.isdisjoint(_words(line))
        reordered.append(
            place.model_copy(
                update={
                    "line": place.line if names_a_worker else line,
                    "ranked_by": RankedBy.AI,
                },
            ),
        )
    return (*reordered, *ranked[len(ai_order) :])


class BestTake5(BaseModel):
    """The best Take 5 of a set, with one line saying what was good about it (W8).

    Attributes:
        take5: The saved Take 5.
        line: One line saying what was good about it.
        picked_by: Whether the AI or the fixed rules picked it and wrote the line.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    take5: SavedTake5
    line: str
    picked_by: RankedBy


def is_careful(take5: SavedTake5) -> bool:
    """Say whether a Take 5 is careful enough to be the best (W8).

    A rushed Take 5 can still be the best: Jake chose on 2026-11-20 that a Take 5
    with good answers is good however quickly it was done.

    Args:
        take5: A saved Take 5.

    Returns:
        True when it is finished, its question was answered, every hazard has
        controls, and only W5 may find a gap. A paper card has no question, so it is
        never the best (P5).
    """
    return (
        take5.is_finished
        and take5.challenge is not None
        and take5.challenge.answer is not None
        and all(hazard.controls for hazard in take5.hazards)
        and all(gap == RUSHED_GAP for gap in thought_gaps(take5))
    )


def best_shortlist(take5s: Sequence[SavedTake5]) -> tuple[SavedTake5, ...]:
    """List the careful Take 5s the best is chosen from, best first by the rules (W8).

    Args:
        take5s: The Take 5s to choose from, in any order.

    Returns:
        Up to `BEST_SHORTLIST_COUNT` careful Take 5s: the riskiest job first, then
        the one that took longest, then the newest.
    """
    newest_first: list[SavedTake5] = sorted(
        (take5 for take5 in take5s if is_careful(take5)),
        key=lambda take5: take5.created_at,
        reverse=True,
    )
    ordered: list[SavedTake5] = sorted(
        newest_first,
        key=lambda take5: (
            highest_score(take5),
            time_taken(take5) or timedelta(0),
        ),
        reverse=True,
    )
    return tuple(ordered[:BEST_SHORTLIST_COUNT])


def best_rule_line(take5: SavedTake5) -> str:
    """Write the line the fixed rules give the best Take 5 (W8).

    Args:
        take5: A careful saved Take 5.

    Returns:
        Such as "Highest risk 18 Extreme, with specific hazards, controls that lower
        each risk and a full answer to the question."
    """
    return (
        f"{_highest_risk_words(take5)}, with specific "
        "hazards, controls that lower each risk and a full answer to the question."
    )


def best_by_rules(take5s: Sequence[SavedTake5]) -> BestTake5 | None:
    """Pick the best Take 5 by the fixed rules alone (W8).

    Args:
        take5s: The Take 5s to choose from.

    Returns:
        The first of the shortlist with its rule line, or None when none is careful.
    """
    shortlist: tuple[SavedTake5, ...] = best_shortlist(take5s)
    if not shortlist:
        return None
    return BestTake5(
        take5=shortlist[0],
        line=best_rule_line(shortlist[0]),
        picked_by=RankedBy.RULES,
    )


def minutes_taken(take5: SavedTake5) -> int | None:
    """Say how many whole minutes a Take 5 took, rounded (W5, W9).

    Args:
        take5: A saved Take 5.

    Returns:
        The minutes from its start to its save, or None when that can't be told.
    """
    taken: timedelta | None = time_taken(take5)
    return _whole(taken.total_seconds() / 60) if taken is not None else None


def typical_minutes(take5s: Sequence[SavedTake5]) -> int | None:
    """Find the typical time a finished Take 5 took: the median, in minutes (W9).

    Args:
        take5s: The Take 5s to look at.

    Returns:
        The median of the finished ones' times, rounded to whole minutes, or None
        when none has a time.
    """
    times: list[float] = [
        taken.total_seconds() / 60
        for take5 in take5s
        if take5.is_finished and (taken := time_taken(take5)) is not None
    ]
    return _whole(statistics.median(times)) if times else None


def _whole(minutes: float) -> int:
    """Round minutes to a whole number, a half going up, as people expect (W9).

    Python's `round()` sends a half to the even number, so 6.5 would be 6.

    Args:
        minutes: The minutes, never negative.

    Returns:
        The nearest whole minute.
    """
    return math.floor(minutes + 0.5)


def best_text(shortlist: Sequence[SavedTake5]) -> str:
    """Write out what the AI is given to pick the best from (W8).

    Args:
        shortlist: The careful Take 5s, numbered from 1 in this order.

    Returns:
        JSON in the same shape as `ranking_text()`, without any worker's name.
    """
    return json.dumps(
        {"take5s": _described(shortlist)},
        indent=2,
        ensure_ascii=False,
    )


class _AiPick(BaseModel):
    """The AI's pick of the best, before it is checked."""

    number: int
    why: str


def checked_ai_pick(reply: str, count: int) -> tuple[int, str] | None:
    """Keep the AI's pick of the best only if it passes W8.

    Args:
        reply: The AI's reply, exactly as it came.
        count: How many Take 5s it was given, numbered 1 to `count`.

    Returns:
        The number picked, with its line; or None when the reply isn't the expected
        JSON, picks a number it wasn't given, or its line fails W6's checks.
    """
    try:
        parsed: _AiPick = _AiPick.model_validate_json(_without_fence(reply))
    except ValueError:
        return None
    line: str = parsed.why.strip()
    if not 1 <= parsed.number <= count or not _is_one_good_line(line):
        return None
    return parsed.number, line


def with_ai_pick(
    shortlist: Sequence[SavedTake5],
    pick: tuple[int, str],
) -> BestTake5:
    """Make the AI's pick the best, with its line unless it names a worker (W8).

    Args:
        shortlist: The careful Take 5s the AI was given, in order.
        pick: The number picked, from 1, with its line.

    Returns:
        The best Take 5, picked by the AI.
    """
    number, line = pick
    take5: SavedTake5 = shortlist[number - 1]
    names_a_worker: bool = not _worker_names(shortlist).isdisjoint(_words(line))
    return BestTake5(
        take5=take5,
        line=best_rule_line(take5) if names_a_worker else line,
        picked_by=RankedBy.AI,
    )
