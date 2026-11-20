"""The Take 5 endpoints. Each one turns HTTP into a service call and holds no rules."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException

from risk_assessment.api.schemas import (
    AnswerRequest,
    ErrorMessage,
    FormErrors,
    SubmissionRequest,
    Take5ListPage,
    Take5Response,
    Take5Summary,
    TemplateResponse,
)
from risk_assessment.domain.controls import ControlKind
from risk_assessment.domain.questions import Answer
from risk_assessment.domain.take5.challenge import AI_NOTICE
from risk_assessment.domain.take5.draft import DraftCheck, Take5Draft
from risk_assessment.domain.take5.fix import offers_a_fix
from risk_assessment.domain.take5.hazard_nudges import HAZARD_AI_NOTICE, Nudge
from risk_assessment.domain.take5.saved import SavedTake5
from risk_assessment.domain.take5.template import Take5Template
from risk_assessment.services.take5s import (
    AlreadyAnsweredError,
    SavedListPage,
    SubmissionConflictError,
    Take5NotFoundError,
    Take5Service,
)

_NOT_FOUND_MESSAGE: str = "This Take 5 could not be found."

# Every error reply a route can send, so the front end's generated types know them.
_UNREADABLE: dict[int | str, dict[str, Any]] = {
    422: {"model": FormErrors, "description": "Something is missing or wrong"},
}
_NOT_FOUND: dict[int | str, dict[str, Any]] = {
    404: {"model": ErrorMessage, "description": "No Take 5 has this ID"},
}
_CONFLICT: dict[int | str, dict[str, Any]] = {
    409: {"model": ErrorMessage, "description": "This ID was used for other answers"},
}
_ANSWERED: dict[int | str, dict[str, Any]] = {
    409: {"model": ErrorMessage, "description": "It was already answered"},
}


def create_router(service: Take5Service) -> APIRouter:
    """Bind each endpoint to the service that the composition root built.

    Args:
        service: The Take 5 service the endpoints call.

    Returns:
        The router with every Take 5 endpoint.
    """
    router = APIRouter(tags=["take5"])

    @router.get("/api/take5/template")
    def get_template() -> TemplateResponse:
        """Return the template a new Take 5 is filled in on, and its choices."""
        template: Take5Template = service.template
        return TemplateResponse(
            name=template.name,
            questions=template.questions,
            answer_choices=tuple(Answer),
            matrix=template.matrix,
            control_kinds=tuple(ControlKind),
            likelihood_guidance=template.likelihood_guidance,
            consequence_guidance=template.consequence_guidance,
            control_guidance=template.control_guidance,
            ai_notice=AI_NOTICE if service.asks_ai else None,
            hazard_ai_notice=(
                HAZARD_AI_NOTICE if service.judges_hazards_with_ai else None
            ),
        )

    @router.post("/api/take5s/check", responses=_UNREADABLE)
    def check(draft: Take5Draft) -> DraftCheck:
        """Return what is missing, the warnings and the ratings, saving nothing."""
        return service.check(draft)

    @router.post("/api/take5s/nudges", responses=_UNREADABLE)
    def nudges(draft: Take5Draft) -> tuple[Nudge, ...]:
        """Return a nudge for each vague hazard linked to a Yes, saving nothing (T6).

        An AI judges the hazards when one is set up, for up to 5 seconds, and the word
        rule decides the rest. The phone asks once for each hazard's words.
        """
        return service.nudges(draft)

    @router.post("/api/take5s", responses=_UNREADABLE | _CONFLICT)
    def submit(request: SubmissionRequest) -> Take5Response:
        """Check and save a Take 5 once, and return it, unfinished, with its question.

        A draft with gaps raises `InvalidDraftError`, which `api/errors.py` turns into
        a 422.
        """
        try:
            saved: SavedTake5 = service.submit(request.draft, request.id)
        except SubmissionConflictError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        return _response(saved, service)

    @router.post(
        "/api/take5s/{take5_id}/answer",
        responses=_UNREADABLE | _NOT_FOUND | _ANSWERED,
    )
    def answer(take5_id: UUID, request: AnswerRequest) -> Take5Response:
        """Save the answer to a Take 5's question, and return it finished.

        An answer that is too short raises `InvalidAnswerError`, which
        `api/errors.py` turns into a 422.
        """
        try:
            finished: SavedTake5 = service.answer(take5_id, request.answer)
        except Take5NotFoundError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        except AlreadyAnsweredError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        return _response(finished, service)

    @router.get("/api/take5s")
    def list_take5s(before: UUID | None = None) -> Take5ListPage:
        """Return 50 saved Take 5s, newest first, each with its saved verdict.

        Args:
            before: The last Take 5 already shown, for the page after it, or None
                for the newest.
        """
        page: SavedListPage = service.saved_list_page(before)
        return Take5ListPage(
            take5s=tuple(
                _summary(saved, saved.id in page.fixed_ids) for saved in page.take5s
            ),
            next=page.next_older_than,
        )

    @router.get("/api/take5s/{take5_id}", responses=_UNREADABLE | _NOT_FOUND)
    def get(take5_id: UUID) -> Take5Response:
        """Return a saved Take 5 with its verdict, or its question if unfinished."""
        saved: SavedTake5 | None = service.get(take5_id)
        if saved is None:
            raise HTTPException(status_code=404, detail=_NOT_FOUND_MESSAGE)
        return _response(saved, service)

    return router


def _summary(saved: SavedTake5, fixed: bool) -> Take5Summary:
    """Build one line of the list from a saved Take 5.

    Args:
        saved: The saved Take 5.
        fixed: Whether a newer Take 5 fixes it.

    Returns:
        Its line in the list.
    """
    return Take5Summary(
        id=saved.id,
        created_at=saved.created_at,
        worker_name=saved.worker_name,
        job=saved.job,
        can_start=saved.verdict.can_start if saved.verdict is not None else None,
        fixed=fixed,
    )


def _response(saved: SavedTake5, service: Take5Service) -> Take5Response:
    """Build the reply for a saved Take 5: its rating, its fix, and if it offers one.

    Args:
        saved: The saved Take 5.
        service: The service that finds its fix.

    Returns:
        The reply.
    """
    fixed_by: UUID | None = service.fixed_by(saved.id)
    return Take5Response(
        take5=saved,
        rating=saved.rating,
        fixed_by=fixed_by,
        offers_fix=offers_a_fix(saved, fixed_by),
    )
