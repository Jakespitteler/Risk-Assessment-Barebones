"""The ranking endpoint. It turns HTTP into a service call and holds no rules."""

from typing import Any

from fastapi import APIRouter
from pydantic import AwareDatetime

from risk_assessment.api.schemas import (
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
                is for "Best and worst of today".
        """
        today: BestAndWorst = service.since(since)
        return RankedTake5s(
            take5s=tuple(_line(ranked) for ranked in today.ranked),
            best=_best_line(today.best) if today.best is not None else None,
            typical_minutes=today.typical_minutes,
        )

    return router


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
