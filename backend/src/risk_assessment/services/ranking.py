"""Rank Take 5s worst first, and find the best (W1 to W9, F10)."""

import logging
import threading
import time
from collections.abc import Callable, Sequence
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import UTC, datetime
from typing import ClassVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from risk_assessment.domain.take5.ranking import (
    AI_RANKED_COUNT,
    AI_RANKING_TIME_LIMIT_SECONDS,
    BestTake5,
    RankedTake5,
    best_by_rules,
    best_shortlist,
    best_text,
    checked_ai_order,
    checked_ai_pick,
    rank_by_rules,
    ranking_text,
    typical_minutes,
    with_ai_order,
    with_ai_pick,
)
from risk_assessment.domain.take5.saved import SavedTake5
from risk_assessment.services.ports import Take5Ranker, Take5Repository

_logger: logging.Logger = logging.getLogger(__name__)

# Rankings are remembered until the server restarts, so opening the page again asks
# the AI again only when a Take 5 was added or finished (decision D95). Only the
# newest few are kept.
_REMEMBERED_RANKINGS: int = 20
# Earlier than any Take 5, so ranking "since" it ranks every one saved (D118).
_EVERY_TAKE5: datetime = datetime.min.replace(tzinfo=UTC)

type _RankingKey = tuple[tuple[UUID, bool], ...]


class BestAndWorst(BaseModel):
    """A set of Take 5s worst first, the best of them, and the typical time taken.

    Attributes:
        ranked: Every one, worst first, each with its line (W1 to W7).
        best: The best careful one with its line, or None when none is careful (W8).
        typical_minutes: The median minutes a finished one took, or None (W9).
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    ranked: tuple[RankedTake5, ...]
    best: BestTake5 | None
    typical_minutes: int | None


class _AiAnswers(BaseModel):
    """What the AI sent back for both jobs, checked, and whether either failed."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    order: tuple[tuple[int, str], ...] | None
    pick: tuple[int, str] | None
    failed: bool


class Take5RankingService:
    """Ranks Take 5s and picks the best by fixed rules, then by the AI if set up."""

    def __init__(
        self,
        repository: Take5Repository,
        ranker: Take5Ranker | None = None,
        ai_time_limit_seconds: float = AI_RANKING_TIME_LIMIT_SECONDS,
        today_only: bool = True,
    ) -> None:
        """Set up the ranking.

        Args:
            repository: Where the Take 5s are kept.
            ranker: The AI that reorders the worst few and picks the best, or None to
                use the fixed rules alone.
            ai_time_limit_seconds: How long to wait for the AI before the fixed rules
                decide.
            today_only: True to rank only the Take 5s since the moment asked for;
                False to rank every saved Take 5, whatever moment is asked for (D118).
        """
        self._today_only: bool = today_only
        self._repository: Take5Repository = repository
        self._ranker: Take5Ranker | None = ranker
        self._ai_time_limit_seconds: float = ai_time_limit_seconds
        self._remembered: dict[_RankingKey, BestAndWorst] = {}
        # Requests run in a pool of threads, so the remembered rankings are locked.
        self._remembered_lock = threading.Lock()

    @property
    def today_only(self) -> bool:
        """Whether only today's Take 5s are ranked, not every saved one (D118)."""
        return self._today_only

    def since(self, earliest: datetime) -> BestAndWorst:
        """Rank the Take 5s started at or after a moment and find the best (W7 to W9).

        A Take 5 counts from when it was started, or when it was saved if it has no
        start time (saved before task 0019), finished or not.

        Args:
            earliest: The moment, such as midnight where the phone is.

        Returns:
            Every one of them worst first, the best, and the typical time taken.
            When the service ranks every saved Take 5, the moment is ignored.
        """
        if not self._today_only:
            earliest = _EVERY_TAKE5
        take5s: tuple[SavedTake5, ...] = tuple(
            take5
            for take5 in self._repository.list_saved_since(earliest)
            if (take5.started_at or take5.created_at) >= earliest
        )
        return self._ranked(take5s)

    def batch(self, take5_ids: Sequence[UUID]) -> BestAndWorst:
        """Rank just these Take 5s, such as a batch of scanned paper cards (F10).

        Args:
            take5_ids: The saved Take 5s to rank. An ID that isn't saved is left out,
                and one given twice counts once.

        Returns:
            Those Take 5s worst first, the best, and the typical time taken.
        """
        take5s: tuple[SavedTake5, ...] = tuple(
            take5
            for take5_id in dict.fromkeys(take5_ids)
            if (take5 := self._repository.get(take5_id)) is not None
        )
        return self._ranked(take5s)

    def _ranked(self, take5s: tuple[SavedTake5, ...]) -> BestAndWorst:
        """Rank some Take 5s by the rules, then the AI, remembering the result.

        Args:
            take5s: The Take 5s to rank.

        Returns:
            Them worst first, the best, and the typical time taken.
        """
        key: _RankingKey = tuple((take5.id, take5.is_finished) for take5 in take5s)
        with self._remembered_lock:
            remembered: BestAndWorst | None = self._remembered.get(key)
        if remembered is not None:
            return remembered
        by_rules: tuple[RankedTake5, ...] = rank_by_rules(take5s)
        worst: tuple[RankedTake5, ...] = by_rules[:AI_RANKED_COUNT]
        shortlist: tuple[SavedTake5, ...] = best_shortlist(take5s)
        answers: _AiAnswers = self._ask_ai(worst, shortlist)
        result = BestAndWorst(
            ranked=(
                by_rules
                if answers.order is None
                else with_ai_order(by_rules, answers.order)
            ),
            best=(
                best_by_rules(take5s)
                if answers.pick is None
                else with_ai_pick(shortlist, answers.pick)
            ),
            typical_minutes=typical_minutes(take5s),
        )
        # A result the rules made because the AI failed isn't kept, so the AI is
        # asked again next time.
        if not answers.failed:
            self._remember(key, result)
        return result

    def _ask_ai(
        self,
        worst: tuple[RankedTake5, ...],
        shortlist: tuple[SavedTake5, ...],
    ) -> _AiAnswers:
        """Ask the AI to order the worst and pick the best, both at once (W6, W8).

        Each job is skipped when there is nothing to choose: fewer than two of the
        worst, or fewer than two careful ones (the one is then the best).

        Args:
            worst: The worst few by the fixed rules.
            shortlist: The careful ones to pick the best from.

        Returns:
            Each job's checked answer, or None for it, and whether either failed.
        """
        ranker: Take5Ranker | None = self._ranker
        if ranker is None:
            return _AiAnswers(order=None, pick=None, failed=False)
        jobs: dict[str, Callable[[], str]] = {}
        if len(worst) >= 2:  # One Take 5 has no order to choose.
            text: str = ranking_text(worst)
            jobs["order"] = lambda: ranker.rank(text)
        if len(shortlist) >= 2:  # One careful Take 5 is the best.
            best: str = best_text(shortlist)
            jobs["pick"] = lambda: ranker.pick_best(best)
        replies: dict[str, str | None] = self._replies(jobs)
        order: tuple[tuple[int, str], ...] | None = None
        pick: tuple[int, str] | None = None
        if (order_reply := replies.get("order")) is not None:
            order = checked_ai_order(order_reply, len(worst))
        if (pick_reply := replies.get("pick")) is not None:
            pick = checked_ai_pick(pick_reply, len(shortlist))
        failed: bool = ("order" in jobs and order is None) or (
            "pick" in jobs and pick is None
        )
        if failed:
            _logger.warning("The AI failed, or its reply failed its checks.")
        return _AiAnswers(order=order, pick=pick, failed=failed)

    def _replies(self, jobs: dict[str, Callable[[], str]]) -> dict[str, str | None]:
        """Run the AI's jobs side by side, giving up on each after the time limit.

        Args:
            jobs: Each job's name and the call that asks the AI.

        Returns:
            Each job's reply, or None when it failed or took too long.
        """
        if not jobs:
            return {}
        # Not a `with` block: leaving one waits for the AI, even after the time limit.
        executor = ThreadPoolExecutor(max_workers=len(jobs))
        try:
            futures: dict[str, Future[str]] = {
                name: executor.submit(call) for name, call in jobs.items()
            }
            deadline: float = time.monotonic() + self._ai_time_limit_seconds
            return {
                name: self._reply(name, future, deadline)
                for name, future in futures.items()
            }
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

    def _reply(self, name: str, future: Future[str], deadline: float) -> str | None:
        """Wait for one job's reply, up to the time limit shared by both jobs.

        Args:
            name: The job, for the log.
            future: The job's reply on its way.
            deadline: When the time limit ends, by `time.monotonic()`.

        Returns:
            The reply, or None when the AI failed or took too long.
        """
        try:
            return future.result(timeout=max(0, deadline - time.monotonic()))
        except Exception:  # Any AI failure at all means the fixed rules decide.
            _logger.warning(
                "The AI could not do the %s job, so the fixed rules did.",
                name,
                exc_info=True,
            )
            return None

    def _remember(self, key: _RankingKey, result: BestAndWorst) -> None:
        """Keep a result for next time, forgetting the oldest beyond the limit.

        Args:
            key: Which Take 5s were ranked, and whether each was finished.
            result: The ranking and the best.
        """
        with self._remembered_lock:
            self._remembered[key] = result
            while len(self._remembered) > _REMEMBERED_RANKINGS:
                del self._remembered[next(iter(self._remembered))]
