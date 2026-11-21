"""The ranking endpoint. It turns HTTP into a service call and holds no rules."""

from typing import Any

from fastapi import APIRouter
from pydantic import AwareDatetime

from risk_assessment.api.schemas import (
    BatchRankingRequest,
    BestTake5Line,
    FormErrors,
    RankedTake5Line,
    RankedTake5s,
)
from risk_assessment.domain.take5.ranking import (
    BestTake5,
    RankedBy,
    RankedTake5,
    minutes_taken,
)
from risk_assessment.domain.take5.saved import SavedTake5
from risk_assessment.services.ranking import BestAndWorst, Take5RankingService

_UNREADABLE: dict[int | str, dict[str, Any]] = {
    422: {"model": FormErrors, "description": "The moment is missing or has no zone"},
}


def create_ranking_router(service: Take5RankingService) -> APIRouter:
    """Bind the ranking endpoint to the service that the composition root built.

    Args:
        service: The ranking service the endpoint calls.

    Returns:
        The router with the ranking endpoint.
    """
    router = APIRouter(tags=["ranking"])

    @router.get("/api/ranked-take5s", responses=_UNREADABLE)
    def ranked_take5s(since: AwareDatetime) -> RankedTake5s:
        """Rank the Take 5s started since a moment, and find the best (W1 to W9).

        Args:
            since: The moment, with its time zone, such as midnight where the phone
                is for "Today's review".
        """
        return _ranked(service.since(since), today_only=service.today_only)

    @router.post("/api/ranked-take5s/batch", responses=_UNREADABLE)
    def ranked_batch(request: BatchRankingRequest) -> RankedTake5s:
        """Rank just these saved Take 5s, such as a batch of paper cards (F10).

        An ID that isn't saved is left out.
        """
        return _ranked(service.batch(request.ids), today_only=False)

    return router


def _ranked(result: BestAndWorst, *, today_only: bool) -> RankedTake5s:
    """Build the ranking's reply.

    Args:
        result: The Take 5s worst first, the best and the typical time.
        today_only: Whether only today's were ranked (D118).

    Returns:
        The reply.
    """
    return RankedTake5s(
        take5s=tuple(_line(ranked) for ranked in result.ranked),
        best=_best_line(result.best) if result.best is not None else None,
        typical_minutes=result.typical_minutes,
        today_only=today_only,
    )


def _line(ranked: RankedTake5) -> RankedTake5Line:
    """Build one line of the ranking.

    Args:
        ranked: A Take 5 and its place.

    Returns:
        Its line on the page.
    """
    take5: SavedTake5 = ranked.take5
    return RankedTake5Line(
        id=take5.id,
        created_at=take5.created_at,
        worker_name=take5.worker_name,
        job=take5.job,
        can_start=take5.verdict.can_start if take5.verdict is not None else None,
        line=ranked.line,
        ranked_by_ai=ranked.ranked_by is RankedBy.AI,
    )


def _best_line(best: BestTake5) -> BestTake5Line:
    """Build the best Take 5's card.

    Args:
        best: The best Take 5 and its line.

    Returns:
        Its card on the page.
    """
    take5: SavedTake5 = best.take5
    return BestTake5Line(
        id=take5.id,
        created_at=take5.created_at,
        worker_name=take5.worker_name,
        job=take5.job,
        can_start=take5.verdict.can_start if take5.verdict is not None else True,
        line=best.line,
        picked_by_ai=best.picked_by is RankedBy.AI,
        minutes_taken=minutes_taken(take5),
    )
