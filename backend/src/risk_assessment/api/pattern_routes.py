"""The patterns-over-time endpoint: HTTP to a service call, holding no rules."""

from typing import Any
from zoneinfo import ZoneInfo

from fastapi import APIRouter

from risk_assessment.api.schemas import FormErrors
from risk_assessment.api.table_routes import ZoneName
from risk_assessment.domain.take5.patterns import Patterns
from risk_assessment.services.patterns import PatternsService

_UNREADABLE: dict[int | str, dict[str, Any]] = {
    422: {"model": FormErrors, "description": "The time zone can't be read"},
}


def create_pattern_router(service: PatternsService) -> APIRouter:
    """Bind the patterns-over-time endpoint to the service the composition root built.

    Args:
        service: The service the endpoint calls.

    Returns:
        The router with the endpoint.
    """
    router = APIRouter(tags=["patterns"])

    @router.get("/api/patterns", responses=_UNREADABLE)
    def patterns(zone: ZoneName) -> Patterns:
        """Find patterns over time in every saved Take 5 (S1 to S5).

        Args:
            zone: The page's time zone, to read a phone's start time in (E3).
        """
        return service.patterns(ZoneInfo(zone))

    return router
