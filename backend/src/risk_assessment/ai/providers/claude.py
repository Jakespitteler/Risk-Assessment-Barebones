"""Claude, from Anthropic, as a `LanguageModel` (spec decision D9).

This file knows nothing about Take 5s. It turns instructions and text into one call
to Anthropic's Messages API and hands back the text of the reply.
"""

import logging
from typing import Literal

import anthropic
from anthropic.types import Message, TextBlock

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
    ) -> None:
        """Set up the client. Nothing is sent until `reply()` is called.

        Args:
            api_key: The key for Anthropic's API.
            model: Which Claude model to use, or None for `DEFAULT_MODEL`.
            effort: How hard the model thinks before it replies. Low keeps a short
                job quick.
            http_client: Tests pass one that never reaches the network. By default
                the library makes its own.
        """
        self.name: str = model or DEFAULT_MODEL
        self._effort: Effort = effort
        self._client = anthropic.Anthropic(
            api_key=api_key,
            timeout=NETWORK_TIME_LIMIT_SECONDS,
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
        message: Message = self._client.messages.create(
            model=self.name,
            max_tokens=MAX_OUTPUT_TOKENS,
            system=instructions,
            messages=[{"role": "user", "content": text}],
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
