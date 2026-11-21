"""Tests for the ranking service: today's Take 5s, the AI and its fallback (W6, W7)."""

import json
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest

from risk_assessment.domain.take5.ranking import RankedBy, RankedTake5
from risk_assessment.domain.take5.saved import SavedTake5
from risk_assessment.services.ranking import BestAndWorst, Take5RankingService
from risk_assessment.storage.sqlite import SqliteTake5Repository
from tests.domain.take5.test_ranking import ranked_take5

MIDNIGHT_IN_PERTH: datetime = datetime(2026, 11, 20, 0, 0, tzinfo=UTC) - timedelta(
    hours=8,
)


FIRST_IS_BEST: str = json.dumps({"number": 1, "why": "Specific controls."})


class StandInRanker:
    """A stand-in AI that sends back set replies, and counts how often it was asked.

    Attributes:
        reply: What it sends back to order the worst.
        best_reply: What it sends back to pick the best.
        texts: Each text it was given to order.
        best_texts: Each text it was given to pick the best from.
    """

    def __init__(
        self,
        reply: str,
        delay_seconds: float = 0,
        best_reply: str = FIRST_IS_BEST,
    ) -> None:
        """Choose the replies.

        Args:
            reply: What it sends back to order the worst.
            delay_seconds: How long it takes.
            best_reply: What it sends back to pick the best.
        """
        self.reply: str = reply
        self.delay_seconds: float = delay_seconds
        self.best_reply: str = best_reply
        self.texts: list[str] = []
        self.best_texts: list[str] = []

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

    def pick_best(self, take5s_text: str) -> str:
        """Record the text and send back the set pick.

        Args:
            take5s_text: The careful Take 5s as the AI is given them.

        Returns:
            The set pick.
        """
        self.best_texts.append(take5s_text)
        time.sleep(self.delay_seconds)
        return self.best_reply


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

    def pick_best(self, take5s_text: str) -> str:
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

    ranked: tuple[RankedTake5, ...] = (
        Take5RankingService(repository).since(MIDNIGHT_IN_PERTH).ranked
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

    ranked: tuple[RankedTake5, ...] = (
        Take5RankingService(
            repository,
            ranker,
        )
        .since(MIDNIGHT_IN_PERTH)
        .ranked
    )

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

    first: tuple[RankedTake5, ...] = service.since(MIDNIGHT_IN_PERTH).ranked
    service._ranker = StandInRanker(SWAPPED)  # pyright: ignore[reportPrivateUsage]
    second: tuple[RankedTake5, ...] = service.since(MIDNIGHT_IN_PERTH).ranked

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

    ranked: tuple[RankedTake5, ...] = service.since(MIDNIGHT_IN_PERTH).ranked

    assert [each.take5.id for each in ranked] == [careless.id, careful.id]


def test_the_same_take5s_are_ranked_once_until_one_is_added(
    repository: SqliteTake5Repository,
) -> None:
    """A ranking is remembered, so opening the page again doesn't ask the AI again."""
    two_today(repository)
    ranker = StandInRanker(SWAPPED)
    service = Take5RankingService(repository, ranker)

    service.since(MIDNIGHT_IN_PERTH)
    service.since(MIDNIGHT_IN_PERTH)
    repository.add(ranked_take5(saved_at=MIDNIGHT_IN_PERTH + timedelta(hours=8)))
    service.since(MIDNIGHT_IN_PERTH)

    assert len(ranker.texts) == 2


def test_one_take5_is_not_sent_to_the_ai(repository: SqliteTake5Repository) -> None:
    """With only one Take 5 there is nothing to order, so the AI isn't asked."""
    repository.add(ranked_take5(saved_at=MIDNIGHT_IN_PERTH + timedelta(hours=7)))
    ranker = StandInRanker(SWAPPED)

    Take5RankingService(repository, ranker).since(MIDNIGHT_IN_PERTH)

    assert ranker.texts == []


def test_the_same_take5s_are_ranked_again_once_one_is_finished(
    repository: SqliteTake5Repository,
) -> None:
    """W7: answering an unfinished Take 5's question changes its ranking."""
    careless, _ = two_today(repository)
    ranker = StandInRanker(SWAPPED)
    service = Take5RankingService(repository, ranker)

    service.since(MIDNIGHT_IN_PERTH)
    finished: SavedTake5 = ranked_take5(
        minutes_taken=1,
        saved_at=careless.created_at,
    ).model_copy(update={"id": careless.id})
    repository.finish(finished)
    service.since(MIDNIGHT_IN_PERTH)

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

    ranked: tuple[RankedTake5, ...] = (
        Take5RankingService(
            repository,
            ranker,
        )
        .since(MIDNIGHT_IN_PERTH)
        .ranked
    )

    assert len(json.loads(ranker.texts[0])["take5s"]) == 10
    assert ranked[-1].take5.id == careful.id
    assert ranked[-1].ranked_by is RankedBy.RULES
    assert [each.ranked_by for each in ranked[:10]] == [RankedBy.AI] * 10


def two_careful_today(
    repository: SqliteTake5Repository,
) -> tuple[SavedTake5, SavedTake5]:
    """Save two careful Take 5s this morning in Perth: 10 minutes, then 3.

    Args:
        repository: Where to save them.

    Returns:
        The 10-minute one, then the 3-minute one.
    """
    morning: datetime = MIDNIGHT_IN_PERTH + timedelta(hours=7)
    slow: SavedTake5 = repository.add(ranked_take5(saved_at=morning))
    quick: SavedTake5 = repository.add(
        ranked_take5(minutes_taken=3, saved_at=morning),
    )
    return slow, quick


def test_the_ai_picks_the_best_of_the_careful_ones(
    repository: SqliteTake5Repository,
) -> None:
    """W8: the AI is given the shortlist and its checked pick is the best."""
    _, quick = two_careful_today(repository)
    ranker = StandInRanker(
        SWAPPED,
        best_reply=json.dumps({"number": 2, "why": "Exact chock points."}),
    )

    today: BestAndWorst = Take5RankingService(repository, ranker).since(
        MIDNIGHT_IN_PERTH,
    )

    assert len(ranker.best_texts) == 1
    assert today.best is not None
    assert today.best.take5.id == quick.id
    assert today.best.line == "Exact chock points."
    assert today.typical_minutes == 7  # The median of 10 and 3 is 6.5, rounded up.


def test_a_failed_ai_pick_leaves_the_rules_best_and_is_asked_again(
    repository: SqliteTake5Repository,
) -> None:
    """W8: a pick that fails its checks isn't remembered, so the AI is asked again."""
    slow, _ = two_careful_today(repository)
    ranker = StandInRanker(SWAPPED, best_reply="Not JSON.")
    service = Take5RankingService(repository, ranker)

    first: BestAndWorst = service.since(MIDNIGHT_IN_PERTH)
    service.since(MIDNIGHT_IN_PERTH)

    assert first.best is not None
    assert first.best.take5.id == slow.id
    assert first.best.picked_by is RankedBy.RULES
    assert len(ranker.best_texts) == 2


def test_a_broken_ai_leaves_both_to_the_rules(
    repository: SqliteTake5Repository,
) -> None:
    """W6, W8: when the AI fails, the rules order the worst and pick the best."""
    slow, _ = two_careful_today(repository)

    today: BestAndWorst = Take5RankingService(repository, BrokenRanker()).since(
        MIDNIGHT_IN_PERTH,
    )

    assert today.best is not None
    assert today.best.take5.id == slow.id
    assert all(each.ranked_by is RankedBy.RULES for each in today.ranked)


def test_one_careful_take5_is_the_best_without_asking_the_ai(
    repository: SqliteTake5Repository,
) -> None:
    """W8: with one careful Take 5 there is nothing to choose between."""
    _, careful = two_today(repository)
    ranker = StandInRanker(SWAPPED)

    today: BestAndWorst = Take5RankingService(repository, ranker).since(
        MIDNIGHT_IN_PERTH,
    )

    assert ranker.best_texts == []
    assert today.best is not None
    assert today.best.take5.id == careful.id


def test_both_ai_jobs_share_one_time_limit(
    repository: SqliteTake5Repository,
) -> None:
    """W6, W8: ordering and picking run side by side, so a slow AI costs one limit."""
    two_careful_today(repository)
    service = Take5RankingService(
        repository,
        StandInRanker(SWAPPED, delay_seconds=2),
        ai_time_limit_seconds=0.5,
    )

    started: float = time.monotonic()
    today: BestAndWorst = service.since(MIDNIGHT_IN_PERTH)
    took: float = time.monotonic() - started

    assert took < 0.9
    assert today.best is not None
    assert today.best.picked_by is RankedBy.RULES


def test_a_batch_ranks_just_its_take5s_once_each_in_any_order(
    repository: SqliteTake5Repository,
) -> None:
    """F10: unknown IDs are left out, repeats count once, and the order sent is moot."""
    careless, careful = two_today(repository)
    repository.add(ranked_take5(saved_at=MIDNIGHT_IN_PERTH + timedelta(hours=8)))
    ranker = StandInRanker(SWAPPED)
    service = Take5RankingService(repository, ranker)

    first: BestAndWorst = service.batch([careful.id, careless.id, careful.id, uuid4()])
    again: BestAndWorst = service.batch([careless.id, careful.id])

    assert {ranked.take5.id for ranked in first.ranked} == {careless.id, careful.id}
    assert again == first
    assert len(ranker.texts) == 1
