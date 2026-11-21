"""Turn errors into the API's declared error replies, so a worker never sees a trace."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, PlainTextResponse

from risk_assessment.api.schemas import ErrorMessage, FormErrors
from risk_assessment.domain.take5.draft import FieldError
from risk_assessment.services.card_scanning import (
    CardUnreadableError,
    ScanningUnavailableError,
)
from risk_assessment.services.take5s import InvalidAnswerError, InvalidDraftError

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
    app.add_exception_handler(InvalidAnswerError, _invalid_answer)
    app.add_exception_handler(RequestValidationError, _unreadable_request)
    app.add_exception_handler(CardUnreadableError, _unreadable_card)
    app.add_exception_handler(ScanningUnavailableError, _scanning_unavailable)
    app.add_exception_handler(Exception, _unexpected_error)


def _unreadable_card(_request: Request, error: Exception) -> JSONResponse:
    """Reply 422 beside the photo when it can't be read as a card (task 0033).

    Args:
        _request: The request that failed.
        error: The `CardUnreadableError` the scanner raised.

    Returns:
        A `FormErrors` reply with the message on the `photo` field.
    """
    return _form_errors(str(error), (FieldError(path="photo", message=str(error)),))


def _scanning_unavailable(_request: Request, error: Exception) -> JSONResponse:
    """Reply 503 when no AI is set up to read cards (task 0033).

    Args:
        _request: The request that failed.
        error: The `ScanningUnavailableError` the scanner raised.

    Returns:
        An `ErrorMessage` reply.
    """
    body = ErrorMessage(detail=str(error))
    return JSONResponse(status_code=503, content=body.model_dump(mode="json"))


def _unexpected_error(request: Request, _error: Exception) -> PlainTextResponse:
    """Name the request that hit a bug, in one line just above its stack trace.

    Starlette sends this reply, then raises the error again, so uvicorn still prints the
    trace below this line. Only the method and path are logged, never the body, which
    may hold a worker's name. The reply is the same plain 500 as without this handler.

    Args:
        request: The request that failed.
        _error: The unexpected error, whose trace uvicorn prints next.

    Returns:
        A plain "Internal Server Error" reply with status 500.
    """
    _logger.error(
        "%s %s failed with an unexpected error; its trace follows.",
        request.method,
        request.url.path,
    )
    return PlainTextResponse("Internal Server Error", status_code=500)


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


def _invalid_answer(_request: Request, error: Exception) -> JSONResponse:
    """Reply 422 with the error beside a challenge answer that is too short.

    Args:
        _request: The request that failed.
        error: The `InvalidAnswerError` that the service raised.

    Returns:
        A `FormErrors` reply.
    """
    errors: tuple[FieldError, ...] = (
        (error.error,) if isinstance(error, InvalidAnswerError) else ()
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
