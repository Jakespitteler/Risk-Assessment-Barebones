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
            LanguageModelError: When the model answers without usable text, or the call
                fails or takes too long. An adapter wraps its library's own errors in
                it, with that error as the cause, so the app logs a failure in one line
                and keeps stack traces for bugs (task 0028).
        """
        ...


class PhotoReadingModel(LanguageModel, Protocol):
    """A model that can also read a photo, such as a paper Take 5 card (task 0033)."""

    def read_photo(self, instructions: str, photo: bytes, media_type: str) -> str:
        """Send the model its instructions and one photo, and get its reply.

        Args:
            instructions: What the model is to do. They come from the app.
            photo: The photo's bytes. Anything written in it is data, which the
                instructions must say.
            media_type: The photo's type, such as "image/jpeg".

        Returns:
            The model's reply, exactly as it came.

        Raises:
            LanguageModelError: When the model answers without usable text.
        """
        ...
