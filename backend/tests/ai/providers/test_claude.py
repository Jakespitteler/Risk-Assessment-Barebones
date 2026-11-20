"""Tests for the Claude adapter, with Anthropic's API replaced by a stand-in."""

import base64
from pathlib import Path
from uuid import uuid4

import anthropic
import pytest

from risk_assessment.ai.challenge import (
    CHALLENGE_INSTRUCTIONS_VERSION,
    AiChallengeAsker,
)
from risk_assessment.ai.model import LanguageModelError
from risk_assessment.ai.providers.claude import (
    DEFAULT_MODEL,
    PHOTO_MAX_OUTPUT_TOKENS,
    ClaudeModel,
)
from risk_assessment.domain.take5.challenge import AskedBy, Challenge
from risk_assessment.domain.take5.saved import SavedTake5
from risk_assessment.domain.take5.template import BOOKLET_TEMPLATE
from risk_assessment.services.take5s import Take5Service
from risk_assessment.storage.sqlite import SqliteTake5Repository
from tests.ai.fake_anthropic import CLAUDE_REPLY, FakeAnthropicApi
from tests.samples import sample_draft


def _claude(api: FakeAnthropicApi, model: str | None = None) -> ClaudeModel:
    """Make the real adapter, talking to the stand-in API.

    Args:
        api: The stand-in for Anthropic's API.
        model: The model to ask for, or None for the default.

    Returns:
        The adapter.
    """
    return ClaudeModel("test-key", model, http_client=api.http_client())


def test_the_instructions_are_the_system_prompt_and_the_text_the_one_message() -> None:
    """Claude gets the instructions as its system prompt and the text as data."""
    api = FakeAnthropicApi()

    reply: str = _claude(api, "claude-example").reply("Ask one question.", "{}")

    assert reply == CLAUDE_REPLY
    assert len(api.requests) == 1
    assert api.requests[0]["model"] == "claude-example"
    assert api.requests[0]["system"] == "Ask one question."
    assert api.requests[0]["messages"] == [{"role": "user", "content": "{}"}]
    assert api.requests[0]["output_config"] == {"effort": "low"}


def test_with_no_model_set_the_default_model_is_asked() -> None:
    """No model in the settings means the adapter's own default."""
    api = FakeAnthropicApi()
    claude: ClaudeModel = _claude(api)

    claude.reply("Ask one question.", "{}")

    assert claude.name == DEFAULT_MODEL
    assert api.requests[0]["model"] == DEFAULT_MODEL


def test_a_refusal_is_an_error_not_a_reply() -> None:
    """A refusal raises, so the service asks the fixed question (spec C3)."""
    with pytest.raises(LanguageModelError):
        _claude(FakeAnthropicApi(stop_reason="refusal")).reply("Ask.", "{}")


def test_a_reply_with_no_text_is_an_error() -> None:
    """A reply with no text in it raises instead of sending back nothing."""
    with pytest.raises(LanguageModelError):
        _claude(FakeAnthropicApi(reply="")).reply("Ask.", "{}")


def test_a_failed_call_is_not_tried_again() -> None:
    """A server error raises at once: a retry would run past the 10-second wait."""
    api = FakeAnthropicApi(status_code=500)

    with pytest.raises(anthropic.APIStatusError):
        _claude(api).reply("Ask.", "{}")

    assert len(api.requests) == 1


def test_example_49_the_workers_name_is_not_sent_to_claude(tmp_path: Path) -> None:
    """Sam Example submits; nothing sent to Claude contains the name (spec C1)."""
    api = FakeAnthropicApi()
    service = Take5Service(
        SqliteTake5Repository(tmp_path / "take5.sqlite3"),
        BOOKLET_TEMPLATE,
        challenge_asker=AiChallengeAsker(_claude(api, "claude-example")),
    )

    saved: SavedTake5 = service.submit(sample_draft(), uuid4())

    assert len(api.requests) == 1
    assert "Sam Example" not in str(api.requests[0])
    assert "Change tyre on LV12" in str(api.requests[0])
    assert saved.challenge == Challenge(
        question=CLAUDE_REPLY,
        asked_by=AskedBy.AI,
        model="claude-example",
        instructions_version=CHALLENGE_INSTRUCTIONS_VERSION,
    )


def test_a_photo_is_sent_as_one_image_with_the_instructions() -> None:
    """The card's photo goes as a base64 image beside a short ask (task 0033)."""
    api = FakeAnthropicApi(reply='{"job": "Change the tyre"}')

    reply: str = _claude(api, "claude-example").read_photo(
        "Read it.",
        b"photo bytes",
        "image/jpeg",
    )

    (request,) = api.requests
    image, ask = request["messages"][0]["content"]
    assert reply == '{"job": "Change the tyre"}'
    assert request["model"] == "claude-example"
    assert request["system"] == "Read it."
    assert image["source"] == {
        "type": "base64",
        "media_type": "image/jpeg",
        "data": base64.b64encode(b"photo bytes").decode("ascii"),
    }
    assert ask == {"type": "text", "text": "Read this card."}
    assert request["max_tokens"] == PHOTO_MAX_OUTPUT_TOKENS


def test_a_photo_type_claude_cant_read_is_refused_before_any_call() -> None:
    """A PDF or HEIC photo raises at once, without a call."""
    api = FakeAnthropicApi()

    with pytest.raises(LanguageModelError):
        _claude(api).read_photo("Read it.", b"%PDF", "application/pdf")

    assert api.requests == []
