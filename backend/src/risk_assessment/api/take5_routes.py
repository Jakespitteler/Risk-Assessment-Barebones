"""The Take 5 endpoints: translate HTTP, then call a service with no rules here."""

from uuid import UUID

from fastapi import APIRouter, HTTPException

from risk_assessment.api.schemas import (
    SubmissionRequest,
    Take5Response,
    TemplateResponse,
)
from risk_assessment.domain.controls import ControlKind
from risk_assessment.domain.take5.draft import DraftCheck, Take5Draft
from risk_assessment.domain.take5.saved import SavedTake5
from risk_assessment.domain.take5.template import (
    BOOKLET_CONSEQUENCE_GUIDANCE,
    BOOKLET_CONTROL_GUIDANCE,
    BOOKLET_LIKELIHOOD_GUIDANCE,
    BOOKLET_TEMPLATE,
)
from risk_assessment.services.take5s import (
    InvalidDraftError,
    SubmissionConflictError,
    Take5Service,
)


def create_router(service: Take5Service) -> APIRouter:
    """Bind each endpoint to the service supplied by the composition root."""
    router = APIRouter(tags=["take5"])

    @router.get("/api/take5/template")
    def get_template() -> TemplateResponse:
        """Return the matrix and every control kind for a new form."""
        return TemplateResponse(
            name=BOOKLET_TEMPLATE.name,
            matrix=BOOKLET_TEMPLATE.matrix,
            control_kinds=tuple(ControlKind),
            likelihood_guidance=BOOKLET_LIKELIHOOD_GUIDANCE,
            consequence_guidance=BOOKLET_CONSEQUENCE_GUIDANCE,
            control_guidance=BOOKLET_CONTROL_GUIDANCE,
        )

    @router.post("/api/take5s/check")
    def check(draft: Take5Draft) -> DraftCheck:
        """Return field errors and ratings without saving the form."""
        return service.check(draft)

    @router.post("/api/take5s")
    def submit(request: SubmissionRequest) -> Take5Response:
        """Save once and return the verdict; incomplete fields remain form errors."""
        try:
            saved: SavedTake5 = service.submit(request.draft, request.id)
        except InvalidDraftError as error:
            raise HTTPException(
                status_code=422, detail=error.check.model_dump(mode="json")
            ) from error
        except SubmissionConflictError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        return Take5Response(take5=saved, rating=saved.rating)

    @router.get("/api/take5s/{take5_id}")
    def get(take5_id: UUID) -> Take5Response:
        """Open the original saved document and verdict."""
        saved: SavedTake5 | None = service.get(take5_id)
        if saved is None:
            raise HTTPException(
                status_code=404, detail="This Take 5 could not be found."
            )
        return Take5Response(take5=saved, rating=saved.rating)

    return router
