"""Tests for the ranking service: today's Take 5s, the AI and its fallback (W6, W7)."""

import json
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from risk_assessment.domain.take5.ranking import RankedBy, RankedTake5
from risk_assessment.domain.take5.saved import SavedTake5
from risk_assessment.services.ranking import Take5RankingService
from risk_assessment.storage.sqlite import SqliteTake5Repository
from tests.domain.take5.test_ranking import ranked_take5

MIDNIGHT_IN_PERTH: datetime = datetime(2026, 11, 20, 0, 0, tzinfo=UTC) - timedelta(
    hours=8,
)


class StandInRanker:
    """A stand-in AI that sends back a set reply, and counts how often it was asked.

    Attributes:
        reply: What it sends back.
        texts: Each text it was given.
    """

    def __init__(self, reply: str, delay_seconds: float = 0) -> None:
        """Choose the reply.

        Args:
            reply: What it sends back.
            delay_seconds: How long it takes.
        """
        self.reply: str = reply
        self.delay_seconds: float = delay_seconds
        self.texts: list[str] = []

    def rank(self, take5s_text: str) -> str:
        """Record the text and send back the set reply.

        Args:
            take5s_text: The Take 5s as the AI is given them.

        Returns:
            The set reply.
        """
        self.texts.append(take5s_text)
        time.sleep(self.delay_seconds)
        return self.reply


class BrokenRanker:
    """A stand-in AI that always fails."""

    def rank(self, take5s_text: str) -> str:
        """Fail.

        Args:
            take5s_text: Not used.

        Raises:
            RuntimeError: Always.
        """
        raise RuntimeError("The AI is down.")


@pytest.fixture
def repository(tmp_path: Path) -> SqliteTake5Repository:
    """Give each test its own empty SQLite database.

    Args:
        tmp_path: pytest's temporary folder for this test.

    Returns:
        The repository.
    """
    return SqliteTake5Repository(tmp_path / "take5.sqlite3")


def two_today(repository: SqliteTake5Repository) -> tuple[SavedTake5, SavedTake5]:
    """Save a careless Take 5 and a careful one, both this morning in Perth.

    Args:
        repository: Where to save them.

    Returns:
        The careless one, then the careful one.
    """
    morning: datetime = MIDNIGHT_IN_PERTH + timedelta(hours=7)
    careless: SavedTake5 = repository.add(
        ranked_take5(answer=None, minutes_taken=1, saved_at=morning),
    )
    careful: SavedTake5 = repository.add(ranked_take5(saved_at=morning))
    return careless, careful


SWAPPED: str = json.dumps(
    {
        "ranking": [
            {"number": 2, "why": "Copied controls."},
            {"number": 1, "why": "Rushed."},
        ],
    },
)


def test_example_100_today_counts_from_the_start_or_else_the_save(
    repository: SqliteTake5Repository,
) -> None:
    """W7: started before midnight is yesterday's; saved after with no start counts."""
    started_late: SavedTake5 = repository.add(
        ranked_take5(saved_at=MIDNIGHT_IN_PERTH + timedelta(minutes=3)),
    )
    no_start_time: SavedTake5 = repository.add(
        ranked_take5(
            minutes_taken=None,
            saved_at=MIDNIGHT_IN_PERTH + timedelta(minutes=1),
        ),
    )
    repository.add(ranked_take5(saved_at=MIDNIGHT_IN_PERTH - timedelta(minutes=1)))

    ranked: tuple[RankedTake5, ...] = Take5RankingService(repository).worst_since(
        MIDNIGHT_IN_PERTH,
    )

    assert started_late.started_at is not None
    assert started_late.started_at < MIDNIGHT_IN_PERTH
    assert [each.take5.id for each in ranked] == [no_start_time.id]


def test_the_ai_reorders_the_worst_and_writes_their_lines(
    repository: SqliteTake5Repository,
) -> None:
    """W6: the AI's checked order and lines are used."""
    careless, careful = two_today(repository)
    ranker = StandInRanker(SWAPPED)

    ranked: tuple[RankedTake5, ...] = Take5RankingService(
        repository,
        ranker,
    ).worst_since(MIDNIGHT_IN_PERTH)

    assert [(each.take5.id, each.line) for each in ranked] == [
        (careful.id, "Copied controls."),
        (careless.id, "Rushed."),
    ]
    assert "Sam Example" not in ranker.texts[0]


def test_a_failed_ai_leaves_the_rules_order_and_is_asked_again(
    repository: SqliteTake5Repository,
) -> None:
    """W6: an AI failure means the fixed rules decide, and it isn't remembered."""
    careless, careful = two_today(repository)
    service = Take5RankingService(repository, BrokenRanker())

    first: tuple[RankedTake5, ...] = service.worst_since(MIDNIGHT_IN_PERTH)
    service._ranker = StandInRanker(SWAPPED)  # pyright: ignore[reportPrivateUsage]
    second: tuple[RankedTake5, ...] = service.worst_since(MIDNIGHT_IN_PERTH)

    assert [each.take5.id for each in first] == [careless.id, careful.id]
    assert all(each.ranked_by is RankedBy.RULES for each in first)
    assert [each.take5.id for each in second] == [careful.id, careless.id]


def test_a_slow_ai_is_given_up_on(repository: SqliteTake5Repository) -> None:
    """W6: an AI slower than the time limit leaves the fixed rules' order."""
    careless, careful = two_today(repository)
    service = Take5RankingService(
        repository,
        StandInRanker(SWAPPED, delay_seconds=0.5),
        ai_time_limit_seconds=0.05,
    )

    ranked: tuple[RankedTake5, ...] = service.worst_since(MIDNIGHT_IN_PERTH)

    assert [each.take5.id for each in ranked] == [careless.id, careful.id]


def test_the_same_take5s_are_ranked_once_until_one_is_added(
    repository: SqliteTake5Repository,
) -> None:
    """A ranking is remembered, so opening the page again doesn't ask the AI again."""
    two_today(repository)
    ranker = StandInRanker(SWAPPED)
    service = Take5RankingService(repository, ranker)

    service.worst_since(MIDNIGHT_IN_PERTH)
    service.worst_since(MIDNIGHT_IN_PERTH)
    repository.add(ranked_take5(saved_at=MIDNIGHT_IN_PERTH + timedelta(hours=8)))
    service.worst_since(MIDNIGHT_IN_PERTH)

    assert len(ranker.texts) == 2


def test_one_take5_is_not_sent_to_the_ai(repository: SqliteTake5Repository) -> None:
    """With only one Take 5 there is nothing to order, so the AI isn't asked."""
    repository.add(ranked_take5(saved_at=MIDNIGHT_IN_PERTH + timedelta(hours=7)))
    ranker = StandInRanker(SWAPPED)

    Take5RankingService(repository, ranker).worst_since(MIDNIGHT_IN_PERTH)

    assert ranker.texts == []


def test_the_same_take5s_are_ranked_again_once_one_is_finished(
    repository: SqliteTake5Repository,
) -> None:
    """W7: answering an unfinished Take 5's question changes its ranking."""
    careless, _ = two_today(repository)
    ranker = StandInRanker(SWAPPED)
    service = Take5RankingService(repository, ranker)

    service.worst_since(MIDNIGHT_IN_PERTH)
    finished: SavedTake5 = ranked_take5(
        minutes_taken=1,
        saved_at=careless.created_at,
    ).model_copy(update={"id": careless.id})
    repository.finish(finished)
    service.worst_since(MIDNIGHT_IN_PERTH)

    assert len(ranker.texts) == 2


def test_only_the_worst_10_go_to_the_ai_and_the_rest_follow(
    repository: SqliteTake5Repository,
) -> None:
    """W6: with 11 Take 5s, the AI orders 10 and the 11th keeps its place by W1."""
    morning: datetime = MIDNIGHT_IN_PERTH + timedelta(hours=7)
    for minute in range(10):
        repository.add(
            ranked_take5(
                answer=None,
                saved_at=morning + timedelta(minutes=minute),
            ),
        )
    careful: SavedTake5 = repository.add(ranked_take5(saved_at=morning))
    reply: str = json.dumps(
        {
            "ranking": [
                {"number": number, "why": "Unanswered."} for number in range(10, 0, -1)
            ],
        },
    )
    ranker = StandInRanker(reply)

    ranked: tuple[RankedTake5, ...] = Take5RankingService(
        repository,
        ranker,
    ).worst_since(MIDNIGHT_IN_PERTH)

    assert len(json.loads(ranker.texts[0])["take5s"]) == 10
    assert ranked[-1].take5.id == careful.id
    assert ranked[-1].ranked_by is RankedBy.RULES
    assert [each.ranked_by for each in ranked[:10]] == [RankedBy.AI] * 10
