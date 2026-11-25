"""ChatGPT, from OpenAI, as a `LanguageModel` (spec decision D9, task 0045).

This file knows nothing about Take 5s. It turns instructions and text into one call
to OpenAI's Responses API and hands back the text of the reply.
"""

import base64
import logging
from typing import Literal

import openai
from openai.types.responses import (
    EasyInputMessageParam,
    Response,
    ResponseInputImageParam,
    ResponseInputItemParam,
    ResponseInputTextParam,
    ResponseOutputMessage,
    ResponseOutputRefusal,
    ResponseOutputText,
)

from risk_assessment.ai.model import LanguageModelError

_logger: logging.Logger = logging.getLogger(__name__)

type Effort = Literal["low", "medium", "high", "xhigh", "max"]

# OpenAI's flagship for complex reasoning, as Claude Opus is for Claude.
DEFAULT_MODEL: str = "gpt-6.2-astra"
# OpenAI's most efficient model, for a short yes-or-no job such as judging whether a
# hazard is vague, as Claude Haiku is for Claude (decision D61).
QUICK_MODEL: str = "gpt-6-luna"
# Where a person makes a key for OpenAI's API.
KEY_PAGE: str = "https://platform.openai.com/api-keys"
# Just over the service's 10 seconds, so a call the service has given up on also
# ends soon, instead of keeping its thread (and a stopping server) waiting.
NETWORK_TIME_LIMIT_SECONDS: float = 11
# Room for the model's thinking as well as a short reply.
MAX_OUTPUT_TOKENS: int = 2000
# The photo types OpenAI's models read (a GIF only if it doesn't move).
PHOTO_TYPES: frozenset[str] = frozenset(
    {"image/jpeg", "image/png", "image/gif", "image/webp"},
)
# Reading a handwritten card takes longer than a short text job (task 0033).
PHOTO_TIME_LIMIT_SECONDS: float = 60
# Room for a whole card written out as JSON, as well as the model's thinking.
PHOTO_MAX_OUTPUT_TOKENS: int = 16000

type _Content = str | list[ResponseInputItemParam]


class ChatGptModel:
    """An OpenAI model reached through OpenAI's API.

    Attributes:
        name: The model's name, such as "gpt-6.2-astra".
    """

    def __init__(
        self,
        api_key: str,
        model: str | None = None,
        effort: Effort = "low",
        http_client: openai.DefaultHttpxClient | None = None,
        network_time_limit_seconds: float = NETWORK_TIME_LIMIT_SECONDS,
    ) -> None:
        """Set up the client. Nothing is sent until `reply()` is called.

        Args:
            api_key: The key for OpenAI's API.
            model: Which OpenAI model to use, or None for `DEFAULT_MODEL`.
            effort: How hard the model thinks before it replies. Low keeps a short
                job quick.
            http_client: Tests pass one that never reaches the network. By default
                the library makes its own.
            network_time_limit_seconds: How long one call may take before it ends,
                just over the service's own limit for the job.
        """
        self.name: str = model or DEFAULT_MODEL
        self._effort: Effort = effort
        self._client = openai.OpenAI(
            api_key=api_key,
            timeout=network_time_limit_seconds,
            max_retries=0,
            http_client=http_client,
        )

    def reply(self, instructions: str, text: str) -> str:
        """Send the model the instructions and the text, and get its reply.

        Args:
            instructions: What the model is to do, sent as its instructions.
            text: What the model works on, sent as the one user message.

        Returns:
            The text of the model's reply.

        Raises:
            LanguageModelError: When the model refuses, doesn't finish, sends back
                no text, or the call fails or takes too long (with the `openai.APIError`
                as its cause).
        """
        return self._send(instructions, text, MAX_OUTPUT_TOKENS, None)

    def read_photo(self, instructions: str, photo: bytes, media_type: str) -> str:
        """Send the model the instructions and one photo, and get its reply.

        Args:
            instructions: What the model is to do, sent as its instructions.
            photo: The photo's bytes, sent as an image.
            media_type: The photo's type, such as "image/jpeg".

        Returns:
            The text of the model's reply.

        Raises:
            LanguageModelError: When the photo's type isn't one the model reads, the
                model refuses, doesn't finish or sends back no text, or the call fails
                or takes longer than `PHOTO_TIME_LIMIT_SECONDS` (with the
                `openai.APIError` as its cause).
        """
        if media_type not in PHOTO_TYPES:
            raise LanguageModelError(f"{self.name} can't read a {media_type} photo.")
        data: str = base64.b64encode(photo).decode("ascii")
        # Handwriting needs the photo's detail, not a small copy of it.
        image: ResponseInputImageParam = {
            "type": "input_image",
            "image_url": f"data:{media_type};base64,{data}",
            "detail": "high",
        }
        ask: ResponseInputTextParam = {"type": "input_text", "text": "Read this card."}
        message: EasyInputMessageParam = {"role": "user", "content": [image, ask]}
        content: list[ResponseInputItemParam] = [message]
        return self._send(
            instructions,
            content,
            PHOTO_MAX_OUTPUT_TOKENS,
            PHOTO_TIME_LIMIT_SECONDS,
        )

    def _send(
        self,
        instructions: str,
        content: _Content,
        max_output_tokens: int,
        time_limit_seconds: float | None,
    ) -> str:
        """Make one call to the Responses API and hand back the reply's text.

        Args:
            instructions: The model's instructions.
            content: The user's input: text, or one message holding an image.
            max_output_tokens: The most the reply may hold, thinking included.
            time_limit_seconds: How long this call may take, or None for the
                client's own limit.

        Returns:
            The text of the model's reply.

        Raises:
            LanguageModelError: When the model refuses, doesn't finish, sends back
                no text, or the call fails or takes too long (with the `openai.APIError`
                as its cause).
        """
        client: openai.OpenAI = (
            self._client
            if time_limit_seconds is None
            else self._client.with_options(timeout=time_limit_seconds)
        )
        try:
            response: Response = client.responses.create(
                model=self.name,
                instructions=instructions,
                input=content,
                max_output_tokens=max_output_tokens,
                reasoning={"effort": self._effort},
                # OpenAI would otherwise keep each call, a card's photo and the
                # worker's name included, for anyone in the project to look up.
                store=False,
            )
        except openai.APIError as error:
            raise LanguageModelError(f"The call to {self.name} failed.") from error
        self._log_usage(response)
        if _refused(response):
            raise LanguageModelError(f"{self.name} refused to reply.")
        if response.status != "completed":
            raise LanguageModelError(
                f"{self.name} didn't finish its reply ({response.status}).",
            )
        reply_text: str = _final_text(response)
        if not reply_text:
            raise LanguageModelError(f"{self.name} sent back no text.")
        return reply_text

    def _log_usage(self, response: Response) -> None:
        """Log how many tokens a call used, as the Claude adapter does.

        Args:
            response: The Responses API's answer.
        """
        if response.usage is None:
            return
        _logger.info(
            "%s replied using %d input and %d output tokens.",
            self.name,
            response.usage.input_tokens,
            response.usage.output_tokens,
            extra={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
        )


def _final_text(response: Response) -> str:
    """Give the text of the model's answer, leaving out any commentary on the way.

    Args:
        response: The Responses API's answer.

    Returns:
        The answer's text, or "" when it has none.
    """
    return "".join(
        part.text
        for item in response.output
        if isinstance(item, ResponseOutputMessage)
        and item.phase in (None, "final_answer")
        for part in item.content
        if isinstance(part, ResponseOutputText)
    )


def _refused(response: Response) -> bool:
    """Say whether the model refused, which OpenAI sends as a part of its reply.

    Args:
        response: The Responses API's answer.

    Returns:
        True when any part of any message is a refusal.
    """
    return any(
        isinstance(part, ResponseOutputRefusal)
        for item in response.output
        if isinstance(item, ResponseOutputMessage)
        for part in item.content
    )
