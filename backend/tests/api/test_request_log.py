"""Tests for keeping the server's request lines to the failed ones (task 0028)."""

import logging

import pytest

from risk_assessment.api.request_log import FailedRequestsOnly


def request_line(status_code: int) -> logging.LogRecord:
    """Make one of uvicorn's request lines.

    Args:
        status_code: The reply's status code.

    Returns:
        The log record, with uvicorn's arguments.
    """
    return logging.LogRecord(
        name="uvicorn.access",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg='%s - "%s %s HTTP/%s" %d',
        args=("127.0.0.1:5000", "GET", "/api/take5s", "1.1", status_code),
        exc_info=None,
    )


@pytest.mark.parametrize(
    ("status_code", "printed"),
    [(200, False), (204, False), (304, False), (404, True), (422, True), (500, True)],
)
def test_only_failed_requests_are_printed(status_code: int, printed: bool) -> None:
    """A 200 while the worker types prints nothing; a 4xx or 5xx prints its line."""
    assert FailedRequestsOnly().filter(request_line(status_code)) is printed


def test_a_line_that_is_not_a_request_line_is_always_printed() -> None:
    """Anything else that reaches the request log is never lost."""
    record = logging.LogRecord(
        name="uvicorn.access",
        level=logging.WARNING,
        pathname=__file__,
        lineno=1,
        msg="Something else happened.",
        args=None,
        exc_info=None,
    )

    assert FailedRequestsOnly().filter(record)
