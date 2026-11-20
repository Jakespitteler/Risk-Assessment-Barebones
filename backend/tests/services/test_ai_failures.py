"""Tests for one-line AI failures, with a trace only for a bug (task 0028)."""

import anthropic
import httpx2
import pytest

from risk_assessment.ai.model import LanguageModelError
from risk_assessment.services.ai_failures import ai_failure_kind, is_expected_ai_failure
from risk_assessment.services.ports import AiReplyError


def provider_failure() -> LanguageModelError:
    """Make what the Claude adapter raises when the call is refused for a bad key.

    Returns:
        The adapter's error, with the provider's own error as its cause.
    """
    request = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    response = httpx2.Response(401, request=request)
    cause = anthropic.AuthenticationError("bad key", response=response, body=None)
    error = LanguageModelError("claude-example could not be reached.")
    error.__cause__ = cause
    return error


@pytest.mark.parametrize(
    ("error", "kind"),
    [
        (TimeoutError(), "it took too long"),
        (LanguageModelError("Claude refused to reply."), "LanguageModelError"),
        (provider_failure(), "AuthenticationError"),
        (TypeError("the text the AI was sent"), "TypeError"),
    ],
)
def test_the_kind_is_named_but_never_the_errors_own_message(
    error: Exception,
    kind: str,
) -> None:
    """A time-out says so; anything else gives its kind or its cause's, not its text."""
    assert ai_failure_kind(error) == kind


def test_only_time_outs_and_the_adapters_errors_are_expected() -> None:
    """Those print one line; anything else is a bug, and keeps its trace."""
    assert is_expected_ai_failure(TimeoutError())
    assert is_expected_ai_failure(AiReplyError("no reply"))
    assert is_expected_ai_failure(provider_failure())
    assert not is_expected_ai_failure(TypeError("a bug"))
    assert not is_expected_ai_failure(KeyError("a bug"))
