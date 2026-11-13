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

    Only the field paths are logged, never the values, which may hold a worker's name.

    Args:
        _request: The request that failed.
        error: The `RequestValidationError` that FastAPI raised.

    Returns:
        A `FormErrors` reply with one error per unreadable field.
    """
    problems: list[FieldError] = []
    if isinstance(error, RequestValidationError):
        for problem in error.errors():
            path: str = ".".join(str(part) for part in problem["loc"][1:])
            problems.append(FieldError(path=path, message=str(problem["msg"])))
    _logger.info("Unreadable request: %s", [problem.path for problem in problems])
    return _form_errors(_BAD_REQUEST_MESSAGE, tuple(problems))


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
