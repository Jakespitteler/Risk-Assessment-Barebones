"""Tests for naming the kind of AI failure in one log line (task 0028)."""

import pytest

from risk_assessment.ai.model import LanguageModelError
from risk_assessment.services.ai_failures import ai_failure_kind


@pytest.mark.parametrize(
    ("error", "kind"),
    [
        (TimeoutError(), "it took too long"),
        (LanguageModelError("Claude refused to reply."), "LanguageModelError"),
        (ConnectionError("the text the AI was sent"), "ConnectionError"),
    ],
)
def test_the_kind_is_named_but_never_the_errors_own_message(
    error: Exception,
    kind: str,
) -> None:
    """A time-out says so; anything else gives its kind, never what it says."""
    assert ai_failure_kind(error) == kind
