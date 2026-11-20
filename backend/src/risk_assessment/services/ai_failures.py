"""Log an AI failure in one line, and keep a stack trace only for a bug (task 0028).

An expected AI failure is handled: the app falls back to the fixed question or the word
rule (spec C3 and T6), so a stack trace would only bury the lines that matter. The line
names the kind of problem, never the provider's own message, which can repeat what the
AI was sent. Anything else raised while asking the AI is a bug in the app's own code,
which can't be fixed without its trace.
"""

from risk_assessment.services.ports import AiReplyError


def is_expected_ai_failure(error: BaseException) -> bool:
    """Say whether an error is one the app expects from an AI, not a bug.

    Args:
        error: What was raised while asking the AI or waiting for its reply.

    Returns:
        True for a time-out, and for an `AiReplyError` an AI adapter raised.
    """
    return isinstance(error, TimeoutError | AiReplyError)


def ai_failure_kind(error: BaseException) -> str:
    """Say in a few words what went wrong when the AI was asked.

    Args:
        error: What was raised while asking the AI or waiting for its reply.

    Returns:
        "it took too long" for a time-out; otherwise the kind of the provider's own
        error when there is one, such as "AuthenticationError", or of the error
        itself, such as "LanguageModelError" or "TypeError".
    """
    if isinstance(error, TimeoutError):
        return "it took too long"
    return type(error.__cause__ or error).__name__
