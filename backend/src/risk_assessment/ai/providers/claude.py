"""Claude, from Anthropic, as a `LanguageModel` (spec decision D9).

This file knows nothing about Take 5s. It turns instructions and text into one call
to Anthropic's Messages API and hands back the text of the reply.
"""

import base64
import logging
from typing import Literal

import anthropic
from anthropic.types import (
    ImageBlockParam,
    Message,
    MessageParam,
    TextBlock,
    TextBlockParam,
)

from risk_assessment.ai.model import LanguageModelError

_logger: logging.Logger = logging.getLogger(__name__)

type Effort = Literal["low", "medium", "high", "xhigh", "max"]

DEFAULT_MODEL: str = "claude-opus-5-5"
# The fastest and cheapest model, for a short yes-or-no job such as judging whether a
# hazard is vague (decision D61).
QUICK_MODEL: str = "claude-haiku-5-5"
# Just over the service's 10 seconds, so a call the service has given up on also
# ends soon, instead of keeping its thread (and a stopping server) waiting.
NETWORK_TIME_LIMIT_SECONDS: float = 11
# Room for the model's thinking as well as a short reply.
MAX_OUTPUT_TOKENS: int = 2000
type PhotoType = Literal["image/jpeg", "image/png", "image/gif", "image/webp"]
# The photo types Claude reads, by the media type the app was sent.
PHOTO_TYPES: dict[str, PhotoType] = {
    "image/jpeg": "image/jpeg",
    "image/png": "image/png",
    "image/gif": "image/gif",
    "image/webp": "image/webp",
}
# Reading a handwritten card takes longer than a short text job (task 0033).
PHOTO_TIME_LIMIT_SECONDS: float = 60
# Room for a whole card written out as JSON, as well as the model's thinking.
PHOTO_MAX_OUTPUT_TOKENS: int = 4000


class ClaudeModel:
    """A Claude model reached through Anthropic's API.

    Attributes:
        name: The model's name, such as "claude-opus-5-5".
    """

    def __init__(
        self,
        api_key: str,
        model: str | None = None,
        effort: Effort = "low",
        http_client: anthropic.DefaultHttpxClient | None = None,
        network_time_limit_seconds: float = NETWORK_TIME_LIMIT_SECONDS,
    ) -> None:
        """Set up the client. Nothing is sent until `reply()` is called.

        Args:
            api_key: The key for Anthropic's API.
            model: Which Claude model to use, or None for `DEFAULT_MODEL`.
            effort: How hard the model thinks before it replies. Low keeps a short
                job quick.
            http_client: Tests pass one that never reaches the network. By default
                the library makes its own.
            network_time_limit_seconds: How long one call may take before it ends,
                just over the service's own limit for the job.
        """
        self.name: str = model or DEFAULT_MODEL
        self._effort: Effort = effort
        self._client = anthropic.Anthropic(
            api_key=api_key,
            timeout=network_time_limit_seconds,
            max_retries=0,
            http_client=http_client,
        )

    def reply(self, instructions: str, text: str) -> str:
        """Send Claude the instructions and the text, and get its reply.

        Args:
            instructions: What Claude is to do, sent as the system prompt.
            text: What Claude works on, sent as the one user message.

        Returns:
            The text of Claude's reply.

        Raises:
            LanguageModelError: When Claude refuses or sends back no text.
            anthropic.APIError: When the call fails or takes too long.
        """
        return self._send(instructions, text, MAX_OUTPUT_TOKENS, None)

    def read_photo(self, instructions: str, photo: bytes, media_type: str) -> str:
        """Send Claude the instructions and one photo, and get its reply.

        Args:
            instructions: What Claude is to do, sent as the system prompt.
            photo: The photo's bytes, sent as an image.
            media_type: The photo's type, such as "image/jpeg".

        Returns:
            The text of Claude's reply.

        Raises:
            LanguageModelError: When the photo's type isn't one Claude reads, or
                Claude refuses or sends back no text.
            anthropic.APIError: When the call fails or takes longer than
                `PHOTO_TIME_LIMIT_SECONDS`.
        """
        photo_type: PhotoType | None = PHOTO_TYPES.get(media_type)
        if photo_type is None:
            raise LanguageModelError(f"{self.name} can't read a {media_type} photo.")
        image: ImageBlockParam = {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": photo_type,
                "data": base64.b64encode(photo).decode("ascii"),
            },
        }
        ask: TextBlockParam = {"type": "text", "text": "Read this card."}
        content: list[ImageBlockParam | TextBlockParam] = [image, ask]
        return self._send(
            instructions,
            content,
            PHOTO_MAX_OUTPUT_TOKENS,
            PHOTO_TIME_LIMIT_SECONDS,
        )

    def _send(
        self,
        instructions: str,
        content: str | list[ImageBlockParam | TextBlockParam],
        max_tokens: int,
        time_limit_seconds: float | None,
    ) -> str:
        """Make one call to the Messages API and hand back the reply's text.

        Args:
            instructions: The system prompt.
            content: The one user message: text, or blocks such as an image.
            max_tokens: The most the reply may hold, thinking included.
            time_limit_seconds: How long this call may take, or None for the
                client's own limit.

        Returns:
            The text of Claude's reply.

        Raises:
            LanguageModelError: When Claude refuses or sends back no text.
            anthropic.APIError: When the call fails or takes too long.
        """
        client: anthropic.Anthropic = (
            self._client
            if time_limit_seconds is None
            else self._client.with_options(timeout=time_limit_seconds)
        )
        user_message: MessageParam = {"role": "user", "content": content}
        message: Message = client.messages.create(
            model=self.name,
            max_tokens=max_tokens,
            system=instructions,
            messages=[user_message],
            output_config={"effort": self._effort},
        )
        _logger.info(
            "%s replied using %d input and %d output tokens.",
            self.name,
            message.usage.input_tokens,
            message.usage.output_tokens,
            extra={
                "input_tokens": message.usage.input_tokens,
                "output_tokens": message.usage.output_tokens,
            },
        )
        if message.stop_reason == "refusal":
            raise LanguageModelError(f"{self.name} refused to reply.")
        reply_text: str = "".join(
            block.text for block in message.content if isinstance(block, TextBlock)
        )
        if not reply_text:
            raise LanguageModelError(f"{self.name} sent back no text.")
        return reply_text
