"""A stand-in for Anthropic's API, so the real Claude adapter runs with no network."""

import json
from typing import Any

import anthropic
import httpx2

CLAUDE_REPLY: str = "What stops the tray moving while you're on it?"


class FakeAnthropicApi:
    """Answers the Claude adapter's calls with a set reply, and records each request.

    Attributes:
        requests: The JSON body of every request the adapter sent, in order.
    """

    def __init__(
        self,
        reply: str = CLAUDE_REPLY,
        stop_reason: str = "end_turn",
        status_code: int = 200,
    ) -> None:
        """Set what the stand-in sends back.

        Args:
            reply: The text of Claude's reply. Empty sends back no text at all.
            stop_reason: Why Claude stopped, such as "end_turn" or "refusal".
            status_code: The HTTP status to answer with.
        """
        self._reply: str = reply
        self._stop_reason: str = stop_reason
        self._status_code: int = status_code
        self.requests: list[dict[str, Any]] = []

    def http_client(self) -> anthropic.DefaultHttpxClient:
        """Make an HTTP client for the adapter that sends every call here.

        Returns:
            A client that never reaches the network.
        """
        return anthropic.DefaultHttpxClient(
            transport=httpx2.MockTransport(self._answer),
        )

    def _answer(self, request: httpx2.Request) -> httpx2.Response:
        """Record one request and answer it.

        Args:
            request: What the adapter sent.

        Returns:
            A Messages API reply, or an error with the set status.
        """
        self.requests.append(json.loads(request.content))
        if self._status_code != 200:
            return httpx2.Response(
                self._status_code,
                json={"type": "error", "error": {"type": "api_error", "message": "x"}},
            )
        content: list[dict[str, str]] = (
            [{"type": "text", "text": self._reply}] if self._reply else []
        )
        return httpx2.Response(
            200,
            json={
                "id": "msg_example",
                "type": "message",
                "role": "assistant",
                "model": "claude-example",
                "content": content,
                "stop_reason": self._stop_reason,
                "stop_sequence": None,
                "usage": {"input_tokens": 1, "output_tokens": 1},
            },
        )
