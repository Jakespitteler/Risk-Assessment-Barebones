"""Keep the server's request lines to the ones that failed (task 0028).

The phone checks the draft and asks for nudges as the worker types, so a line for every
`200 OK` would bury the line that matters. `backend/dev_logging.json` puts this filter
on uvicorn's request log. A line keeps only the path, never the query: the table's
search can hold a worker's name (task 0043), which is never logged.
"""

import logging

# Uvicorn's request line gives these, in this order, as the log record's arguments.
_PATH_POSITION: int = 2
_STATUS_CODE_POSITION: int = 4
_FIRST_FAILED_STATUS: int = 400


class FailedRequestsOnly(logging.Filter):
    """Let a failed request's line through (4xx or 5xx), without its query."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Say whether to print one of uvicorn's request lines.

        Args:
            record: The request line, with uvicorn's arguments: the client, the method,
                the path, the HTTP version and the status code.

        Returns:
            True for a failed request, and for any line that isn't a request line. A
            failed request's path loses its query.
        """
        arguments: object = record.args
        if not isinstance(arguments, tuple) or len(arguments) <= _STATUS_CODE_POSITION:
            return True
        status_code: object = arguments[_STATUS_CODE_POSITION]
        if isinstance(status_code, int) and status_code < _FIRST_FAILED_STATUS:
            return False
        fields: list[object] = list(arguments)
        path: object = fields[_PATH_POSITION]
        if isinstance(path, str):
            fields[_PATH_POSITION] = path.split("?", 1)[0]
            record.args = tuple(fields)
        return True
