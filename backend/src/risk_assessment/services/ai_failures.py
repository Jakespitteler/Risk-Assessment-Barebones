"""Name the kind of problem when the AI fails, in a line without a stack trace.

An AI failure is expected and handled: the app falls back to the fixed question or the
word rule (spec C3 and T6), so a stack trace would only bury the lines that matter
(task 0028). The line names the kind of problem, never the provider's own message,
which can repeat what the AI was sent.
"""


def ai_failure_kind(error: BaseException) -> str:
    """Say in a few words what went wrong when the AI was asked.

    Args:
        error: What was raised while asking the AI or waiting for its reply.

    Returns:
        "it took too long" for a time-out, otherwise the error's kind, such as
        "APIConnectionError" or "AuthenticationError".
    """
    if isinstance(error, TimeoutError):
        return "it took too long"
    return type(error).__name__
