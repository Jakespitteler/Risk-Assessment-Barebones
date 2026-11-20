"""The risk-by-area endpoint. It turns HTTP into a service call and holds no rules."""

from typing import Any

from fastapi import APIRouter
from pydantic import AwareDatetime

from risk_assessment.api.schemas import FormErrors, RiskByArea
from risk_assessment.services.areas import AreaRiskService

_UNREADABLE: dict[int | str, dict[str, Any]] = {
    422: {"model": FormErrors, "description": "The moment is missing or has no zone"},
}


def create_area_router(service: AreaRiskService) -> APIRouter:
    """Bind the risk-by-area endpoint to the service that the composition root built.

    Args:
        service: The service the endpoint calls.

    Returns:
        The router with the endpoint.
    """
    router = APIRouter(tags=["areas"])

    @router.get("/api/risk-by-area", responses=_UNREADABLE)
    def risk_by_area(today: AwareDatetime) -> RiskByArea:
        """Group the last 30 days of Take 5s by area, hottest first (A1 to A5).

        Args:
            today: Midnight today where the phone is, with its time zone.
        """
        return RiskByArea(areas=service.last_30_days(today))

    return router
