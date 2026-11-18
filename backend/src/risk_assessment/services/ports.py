"""What the Take 5 service needs from the world outside: storage and an AI."""

from typing import Protocol
from uuid import UUID

from risk_assessment.domain.take5.challenge import AiQuestion
from risk_assessment.domain.take5.saved import SavedTake5


class Take5Repository(Protocol):
    """Where Take 5s are kept.

    A Take 5 is saved unfinished. Its question is added once and its answer once, and
    a finished Take 5 is never replaced or changed (spec C6).
    """

    def add(self, take5: SavedTake5) -> SavedTake5:
        """Save a Take 5, unless one with the same ID is already saved.

        Args:
            take5: The Take 5 to save.

        Returns:
            The Take 5 now saved with this ID: this one, or the one saved first.
        """
        ...

    def save_question(self, take5: SavedTake5) -> SavedTake5:
        """Replace an unfinished Take 5 that has no question yet with this one.

        Args:
            take5: The Take 5 with its question added.

        Returns:
            The Take 5 now saved with this ID: this one, or the one already there if
            it had a question or was finished.
        """
        ...

    def finish(self, take5: SavedTake5) -> SavedTake5:
        """Replace an unfinished Take 5 with this finished one.

        Args:
            take5: The Take 5 with its answer, verdict and `finished_at`.

        Returns:
            The Take 5 now saved with this ID: this one, or the one already there if
            it was finished first.
        """
        ...

    def get(self, take5_id: UUID) -> SavedTake5 | None:
        """Get a saved Take 5.

        Args:
            take5_id: The Take 5's ID.

        Returns:
            The saved Take 5, or None if there is none with this ID.
        """
        ...

    def list_newest_first(self) -> tuple[SavedTake5, ...]:
        """Get every saved Take 5, the newest first.

        Returns:
            The saved Take 5s, newest first. Two saved at the same moment keep the
            order they were saved in, the later one first.
        """
        ...

    def fixed_by(self, take5_id: UUID) -> UUID | None:
        """Find the newest saved Take 5 whose `fixes` is this ID.

        Args:
            take5_id: The ID of the Take 5 that may have been fixed.

        Returns:
            The newest fix's ID, or None if there is none.
        """
        ...


class ChallengeAsker(Protocol):
    """Anything that can write the challenge question: an AI, or a stand-in in tests."""

    def ask(self, take5_text: str) -> AiQuestion:
        """Write one question about the weakest part of a Take 5 (spec C1).

        Args:
            take5_text: The Take 5 as `challenge_text()` writes it out. It never holds
                the worker's name.

        Returns:
            The reply, which the service checks before it is shown (spec C2).
        """
        ...
