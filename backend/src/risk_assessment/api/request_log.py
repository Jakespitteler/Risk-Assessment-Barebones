"""Keep the server's request lines to the ones that failed (task 0028).

The phone checks the draft and asks for nudges as the worker types, so a line for every
`200 OK` would bury the line that matters. `backend/dev_logging.json` puts this filter
on uvicorn's request log.
"""

import logging

# Uvicorn's request line gives these, in this order, as the log record's arguments.
_STATUS_CODE_POSITION: int = 4
_FIRST_FAILED_STATUS: int = 400


class FailedRequestsOnly(logging.Filter):
    """Let a request line through only when the request failed (4xx or 5xx)."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Say whether to print one of uvicorn's request lines.

        Args:
            record: The request line, with uvicorn's arguments: the client, the method,
                the path, the HTTP version and the status code.

        Returns:
            True for a failed request, and for any line that isn't a request line.
        """
        arguments: object = record.args
        if not isinstance(arguments, tuple) or len(arguments) <= _STATUS_CODE_POSITION:
            return True
        status_code: object = arguments[_STATUS_CODE_POSITION]
        return not isinstance(status_code, int) or status_code >= _FIRST_FAILED_STATUS
