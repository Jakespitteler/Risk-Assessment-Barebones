"""Rank the Take 5s started since a moment worst first (spec W1 to W7)."""

import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from uuid import UUID

from risk_assessment.domain.take5.ranking import (
    AI_RANKED_COUNT,
    AI_RANKING_TIME_LIMIT_SECONDS,
    RankedBy,
    RankedTake5,
    checked_ai_order,
    rank_by_rules,
    ranking_text,
    with_ai_order,
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


class Take5RankingService:
    """Ranks saved Take 5s with the fixed rules, then the AI when one is set up."""

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
            ranker: The AI that reorders the worst few, or None to use the fixed rules
                alone.
            ai_time_limit_seconds: How long to wait for the AI before the fixed rules
                decide.
            today_only: True to rank only the Take 5s since the moment asked for;
                False to rank every saved Take 5, whatever moment is asked for (D118).
        """
        self._today_only: bool = today_only
        self._repository: Take5Repository = repository
        self._ranker: Take5Ranker | None = ranker
        self._ai_time_limit_seconds: float = ai_time_limit_seconds
        self._remembered: dict[_RankingKey, tuple[RankedTake5, ...]] = {}
        # Requests run in a pool of threads, so the remembered rankings are locked.
        self._remembered_lock = threading.Lock()

    @property
    def today_only(self) -> bool:
        """Whether only today's Take 5s are ranked, not every saved one (D118)."""
        return self._today_only

    def worst_since(self, earliest: datetime) -> tuple[RankedTake5, ...]:
        """Rank the Take 5s started at or after a moment, worst first (W7).

        A Take 5 counts from when it was started, or when it was saved if it has no
        start time (saved before task 0019), finished or not.

        Args:
            earliest: The moment, such as midnight where the phone is.

        Returns:
            Every one of them, worst first, each with its line. When the service
            ranks every saved Take 5, the moment is ignored.
        """
        if not self._today_only:
            earliest = _EVERY_TAKE5
        take5s: tuple[SavedTake5, ...] = tuple(
            take5
            for take5 in self._repository.list_saved_since(earliest)
            if (take5.started_at or take5.created_at) >= earliest
        )
        key: _RankingKey = tuple((take5.id, take5.is_finished) for take5 in take5s)
        with self._remembered_lock:
            remembered: tuple[RankedTake5, ...] | None = self._remembered.get(key)
        if remembered is not None:
            return remembered
        ranked: tuple[RankedTake5, ...] = self._rank(take5s)
        # A ranking the rules made because the AI failed isn't kept, so the AI is
        # asked again next time.
        if self._ranker is None or any(
            each.ranked_by is RankedBy.AI for each in ranked
        ):
            self._remember(key, ranked)
        return ranked

    def _rank(self, take5s: tuple[SavedTake5, ...]) -> tuple[RankedTake5, ...]:
        """Rank by the fixed rules, then let the AI reorder the worst few (W1, W6).

        Args:
            take5s: The Take 5s to rank.

        Returns:
            The ranking, worst first.
        """
        by_rules: tuple[RankedTake5, ...] = rank_by_rules(take5s)
        worst: tuple[RankedTake5, ...] = by_rules[:AI_RANKED_COUNT]
        if self._ranker is None or len(worst) < 2:
            return by_rules
        ai_order: tuple[tuple[int, str], ...] | None = self._ai_order(worst)
        if ai_order is None:
            return by_rules
        return with_ai_order(by_rules, ai_order)

    def _ai_order(
        self,
        worst: tuple[RankedTake5, ...],
    ) -> tuple[tuple[int, str], ...] | None:
        """Ask the AI to order the worst few, giving up after the time limit.

        Args:
            worst: The worst few by the fixed rules. Never their workers' names are
                sent (W6).

        Returns:
            The AI's checked order and lines, or None when there is no AI, it fails,
            takes longer than the time limit, or its reply fails W6.
        """
        if self._ranker is None:
            return None
        text: str = ranking_text(worst)
        # Not a `with` block: leaving one waits for the AI, even after the time limit.
        executor = ThreadPoolExecutor(max_workers=1)
        try:
            reply = executor.submit(self._ranker.rank, text)
            order: tuple[tuple[int, str], ...] | None = checked_ai_order(
                reply.result(timeout=self._ai_time_limit_seconds),
                len(worst),
            )
        except Exception:  # Any AI failure at all means the fixed rules decide.
            _logger.warning(
                "The AI could not rank the Take 5s, so the fixed rules did.",
                exc_info=True,
            )
            return None
        finally:
            executor.shutdown(wait=False, cancel_futures=True)
        if order is None:
            _logger.warning("The AI's ranking failed its checks, so the rules decided.")
        return order

    def _remember(self, key: _RankingKey, ranked: tuple[RankedTake5, ...]) -> None:
        """Keep a ranking for next time, forgetting the oldest beyond the limit.

        Args:
            key: Which Take 5s were ranked, and whether each was finished.
            ranked: The ranking.
        """
        with self._remembered_lock:
            self._remembered[key] = ranked
            while len(self._remembered) > _REMEMBERED_RANKINGS:
                del self._remembered[next(iter(self._remembered))]
