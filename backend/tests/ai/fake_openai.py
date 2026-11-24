"""A stand-in for OpenAI's API, so the real ChatGPT adapter runs with no network."""

import json
from typing import Any

import httpx2

CHATGPT_REPLY: str = "What stops the tray moving while you're on it?"


class FakeOpenAiApi:
    """Answers the ChatGPT adapter's calls with a set reply, and records each request.

    Attributes:
        requests: The JSON body of every request the adapter sent, in order.
        read_time_limits: The seconds each request would wait for its answer.
    """

    def __init__(
        self,
        reply: str = CHATGPT_REPLY,
        *,
        refuse: bool = False,
        status: str = "completed",
        status_code: int = 200,
    ) -> None:
        """Set what the stand-in sends back.

        Args:
            reply: The text of the model's reply. Empty sends back no text at all.
            refuse: Whether the reply is a refusal instead of text.
            status: The response's status, such as "completed" or "incomplete".
            status_code: The HTTP status to answer with.
        """
        self._reply: str = reply
        self._refuse: bool = refuse
        self._status: str = status
        self._status_code: int = status_code
        self.requests: list[dict[str, Any]] = []
        self.read_time_limits: list[float | None] = []

    def http_client(self) -> httpx2.Client:
        """Make an HTTP client for the adapter that sends every call here.

        Returns:
            A client that never reaches the network.
        """
        return httpx2.Client(transport=httpx2.MockTransport(self._answer))

    def _answer(self, request: httpx2.Request) -> httpx2.Response:
        """Record one request and answer it.

        Args:
            request: What the adapter sent.

        Returns:
            A Responses API reply, or an error with the set status.
        """
        self.requests.append(json.loads(request.content))
        self.read_time_limits.append(request.extensions["timeout"]["read"])
        if self._status_code != 200:
            return httpx2.Response(
                self._status_code,
                json={"error": {"type": "server_error", "message": "x"}},
            )
        return httpx2.Response(200, json=self._response())

    def _response(self) -> dict[str, Any]:
        """Build the Responses API's answer.

        Returns:
            Its JSON body.
        """
        part: list[dict[str, Any]] = []
        if self._refuse:
            part = [{"type": "refusal", "refusal": "I can't help with that."}]
        elif self._reply:
            part = [{"type": "output_text", "text": self._reply, "annotations": []}]
        return {
            "id": "resp_example",
            "object": "response",
            "created_at": 1_700_000_000,
            "model": "gpt-example",
            "status": self._status,
            "incomplete_details": (
                {"reason": "max_output_tokens"}
                if self._status == "incomplete"
                else None
            ),
            "output": [
                {
                    "type": "message",
                    "id": "msg_example",
                    "role": "assistant",
                    "status": "completed",
                    "content": part,
                },
            ],
            "parallel_tool_calls": False,
            "tool_choice": "auto",
            "tools": [],
            "usage": {
                "input_tokens": 1,
                "output_tokens": 1,
                "total_tokens": 2,
                "input_tokens_details": {"cached_tokens": 0},
                "output_tokens_details": {"reasoning_tokens": 0},
            },
        }
