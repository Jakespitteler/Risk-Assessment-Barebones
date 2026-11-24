"""Tests for the ChatGPT adapter, with OpenAI's API replaced by a stand-in (0045)."""

import base64
from pathlib import Path
from uuid import uuid4

import openai
import pytest

from risk_assessment.ai.challenge import (
    CHALLENGE_INSTRUCTIONS_VERSION,
    AiChallengeAsker,
)
from risk_assessment.ai.model import LanguageModelError
from risk_assessment.ai.providers.chatgpt import (
    DEFAULT_MODEL,
    PHOTO_MAX_OUTPUT_TOKENS,
    PHOTO_TIME_LIMIT_SECONDS,
    ChatGptModel,
)
from risk_assessment.domain.take5.challenge import AskedBy, Challenge
from risk_assessment.domain.take5.saved import SavedTake5
from risk_assessment.domain.take5.template import BOOKLET_TEMPLATE
from risk_assessment.services.take5s import Take5Service
from risk_assessment.storage.sqlite import SqliteTake5Repository
from tests.ai.fake_openai import CHATGPT_REPLY, FakeOpenAiApi
from tests.samples import sample_draft


def _chatgpt(api: FakeOpenAiApi, model: str | None = None) -> ChatGptModel:
    """Make the real adapter, talking to the stand-in API.

    Args:
        api: The stand-in for OpenAI's API.
        model: The model to ask for, or None for the default.

    Returns:
        The adapter.
    """
    return ChatGptModel("test-key", model, http_client=api.http_client())


def test_the_instructions_are_the_instructions_and_the_text_the_input() -> None:
    """The model gets the instructions as its instructions and the text as data."""
    api = FakeOpenAiApi()

    reply: str = _chatgpt(api, "gpt-example").reply("Ask one question.", "{}")

    assert reply == CHATGPT_REPLY
    assert len(api.requests) == 1
    assert api.requests[0]["model"] == "gpt-example"
    assert api.requests[0]["instructions"] == "Ask one question."
    assert api.requests[0]["input"] == "{}"
    assert api.requests[0]["reasoning"] == {"effort": "low"}


def test_with_no_model_set_the_default_model_is_asked() -> None:
    """No model in the settings means the adapter's own default."""
    api = FakeOpenAiApi()
    chatgpt: ChatGptModel = _chatgpt(api)

    chatgpt.reply("Ask one question.", "{}")

    assert chatgpt.name == DEFAULT_MODEL
    assert api.requests[0]["model"] == DEFAULT_MODEL


def test_a_refusal_is_an_error_not_a_reply() -> None:
    """A refusal raises, so the service asks the fixed question (spec C3)."""
    with pytest.raises(LanguageModelError):
        _chatgpt(FakeOpenAiApi(refuse=True)).reply("Ask.", "{}")


def test_a_reply_cut_off_before_it_finished_is_an_error() -> None:
    """A reply that ran out of room may be half a question, so it isn't used."""
    with pytest.raises(LanguageModelError):
        _chatgpt(FakeOpenAiApi(status="incomplete")).reply("Ask.", "{}")


def test_a_reply_with_no_text_is_an_error() -> None:
    """A reply with no text in it raises instead of sending back nothing."""
    with pytest.raises(LanguageModelError):
        _chatgpt(FakeOpenAiApi(reply="")).reply("Ask.", "{}")


def test_a_failed_call_is_not_tried_again() -> None:
    """A server error raises at once: a retry would run past the 10-second wait."""
    api = FakeOpenAiApi(status_code=500)

    with pytest.raises(LanguageModelError) as failure:
        _chatgpt(api).reply("Ask.", "{}")

    assert isinstance(failure.value.__cause__, openai.APIStatusError)
    assert len(api.requests) == 1


def test_example_49_the_workers_name_is_not_sent_to_chatgpt(tmp_path: Path) -> None:
    """Sam Example submits; nothing sent to ChatGPT holds the name (spec C1)."""
    api = FakeOpenAiApi()
    service = Take5Service(
        SqliteTake5Repository(tmp_path / "take5.sqlite3"),
        BOOKLET_TEMPLATE,
        challenge_asker=AiChallengeAsker(_chatgpt(api, "gpt-example")),
    )

    saved: SavedTake5 = service.submit(sample_draft(), uuid4())

    assert len(api.requests) == 1
    assert "Sam Example" not in str(api.requests[0])
    assert "Change tyre on LV12" in str(api.requests[0])
    assert saved.challenge == Challenge(
        question=CHATGPT_REPLY,
        asked_by=AskedBy.AI,
        model="gpt-example",
        instructions_version=CHALLENGE_INSTRUCTIONS_VERSION,
    )


def test_a_photo_is_sent_as_one_image_with_the_instructions() -> None:
    """The card's photo goes as a base64 image beside a short ask (task 0033)."""
    api = FakeOpenAiApi(reply='{"job": "Change the tyre"}')

    reply: str = _chatgpt(api, "gpt-example").read_photo(
        "Read it.",
        b"photo bytes",
        "image/jpeg",
    )

    (request,) = api.requests
    image, ask = request["input"][0]["content"]
    photo: str = base64.b64encode(b"photo bytes").decode("ascii")
    assert reply == '{"job": "Change the tyre"}'
    assert request["model"] == "gpt-example"
    assert request["instructions"] == "Read it."
    assert request["input"][0]["role"] == "user"
    assert image == {
        "type": "input_image",
        "image_url": f"data:image/jpeg;base64,{photo}",
        "detail": "high",
    }
    assert ask == {"type": "input_text", "text": "Read this card."}
    assert request["max_output_tokens"] == PHOTO_MAX_OUTPUT_TOKENS
    assert api.read_time_limits == [PHOTO_TIME_LIMIT_SECONDS]


def test_a_photo_type_chatgpt_cant_read_is_refused_before_any_call() -> None:
    """A PDF or HEIC photo raises at once, without a call."""
    api = FakeOpenAiApi()

    with pytest.raises(LanguageModelError):
        _chatgpt(api).read_photo("Read it.", b"%PDF", "application/pdf")

    assert api.requests == []
