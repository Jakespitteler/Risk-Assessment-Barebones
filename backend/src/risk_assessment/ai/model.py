"""What every AI provider must offer the app: instructions and text in, text out.

A provider's adapter (in `providers/`) imports only this file from the app, so adding
ChatGPT, Gemini or a model a company runs itself means one new adapter file and no
other change to the AI's jobs.
"""

from typing import Protocol

from risk_assessment.services.ports import AiReplyError


class LanguageModelError(AiReplyError):
    """A model gave no text the app can use: a refusal, no text, or no reply at all.

    For a call that failed, the provider's own error is its cause, which names the kind
    of problem in the log, such as `AuthenticationError`.
    """


class LanguageModel(Protocol):
    """Any AI model that is given instructions and text, and replies with text."""

    @property
    def name(self) -> str:
        """The model's name, saved with each question it writes (spec C5)."""
        ...

    def reply(self, instructions: str, text: str) -> str:
        """Send the model its instructions and one piece of text, and get its reply.

        Args:
            instructions: What the model is to do. They come from the app, never
                from the worker.
            text: What the model works on. It may hold the worker's own words, so
                the instructions must treat it as data.

        Returns:
            The model's reply, exactly as it came.

        Raises:
            LanguageModelError: When the model answers without usable text.
        """
        ...
