"""Turn errors into the API's declared error replies, so a worker never sees a trace."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from risk_assessment.api.schemas import FormErrors
from risk_assessment.domain.take5.draft import FieldError
from risk_assessment.services.take5s import InvalidDraftError

_logger: logging.Logger = logging.getLogger(__name__)

_BAD_REQUEST_MESSAGE: str = "Some of what was sent could not be read."
_BAD_FIELD_MESSAGE: str = "This answer could not be read."
# Where FastAPI found a field, which is not part of the field's own path.
_REQUEST_PARTS: tuple[str, ...] = ("body", "path", "query")


def add_error_handlers(app: FastAPI) -> None:
    """Give every 422 the one `FormErrors` shape declared in the API description.

    Args:
        app: The app to add the handlers to.
    """
    app.add_exception_handler(InvalidDraftError, _invalid_draft)
    app.add_exception_handler(RequestValidationError, _unreadable_request)


def _invalid_draft(_request: Request, error: Exception) -> JSONResponse:
    """Reply 422 with the field errors from a draft that can't be submitted yet.

    Args:
        _request: The request that failed.
        error: The `InvalidDraftError` that the service raised.

    Returns:
        A `FormErrors` reply.
    """
    errors: tuple[FieldError, ...] = (
        error.check.errors if isinstance(error, InvalidDraftError) else ()
    )
    return _form_errors(str(error), errors)


def _unreadable_request(_request: Request, error: Exception) -> JSONResponse:
    """Reply 422 when FastAPI can't read a request, such as a malformed ID.

    Each path is written as the draft's own field paths are, such as `worker_name`, so
    the phone can show it beside its field. Only the paths are logged, never the values,
    which may hold a worker's name.

    Args:
        _request: The request that failed.
        error: The `RequestValidationError` that FastAPI raised.

    Returns:
        A `FormErrors` reply with one error per unreadable field.
    """
    problems: list[FieldError] = []
    if isinstance(error, RequestValidationError):
        for problem in error.errors():
            path: str = _field_path(tuple(problem["loc"]))
            problems.append(FieldError(path=path, message=_BAD_FIELD_MESSAGE))
    _logger.info("Unreadable request: %s", [problem.path for problem in problems])
    return _form_errors(_BAD_REQUEST_MESSAGE, tuple(problems))


def _field_path(location: tuple[object, ...]) -> str:
    """Turn where FastAPI found a problem into a dotted field path.

    Args:
        location: FastAPI's location, such as `("body", "draft", "worker_name")`.

    Returns:
        The field's path, such as `worker_name`. A submission's draft fields lose their
        `draft.` prefix, so they match the paths that checking a draft gives.
    """
    parts: list[str] = [str(part) for part in location]
    if parts and parts[0] in _REQUEST_PARTS:
        parts = parts[1:]
    if parts and parts[0] == "draft":
        parts = parts[1:]
    return ".".join(parts)


def _form_errors(detail: str, errors: tuple[FieldError, ...]) -> JSONResponse:
    """Build a 422 reply in the `FormErrors` shape.

    Args:
        detail: The summary for the top of the screen.
        errors: The field errors.

    Returns:
        The JSON reply.
    """
    body = FormErrors(detail=detail, errors=errors)
    return JSONResponse(status_code=422, content=body.model_dump(mode="json"))
