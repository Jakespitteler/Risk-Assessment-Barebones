"""What the Take 5 service needs from the world outside: storage and AI jobs."""

from collections.abc import Collection
from datetime import datetime
from typing import Protocol
from uuid import UUID

from risk_assessment.domain.take5.challenge import AiQuestion
from risk_assessment.domain.take5.saved import SavedTake5


class AiReplyError(Exception):
    """The AI couldn't give a usable reply: it refused, sent nothing, or wasn't reached.

    The service expects this and falls back (spec C3, T6), so it logs one line without
    a stack trace. Any other error from asking the AI is a bug, and keeps its trace
    (task 0028). An AI adapter raises this, or a kind of it, with the provider's own
    error as its cause.
    """


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

    def list_newest_first(
        self,
        older_than: UUID | None = None,
        limit: int | None = None,
    ) -> tuple[SavedTake5, ...]:
        """Get saved Take 5s, the newest first.

        Args:
            older_than: Only those listed after this Take 5, or None to start at the
                newest. A Take 5 saved since can't shift what comes after it. None
                are listed after a Take 5 that isn't saved.
            limit: At most this many, or None for all of them.

        Returns:
            The saved Take 5s, newest first. Two saved at the same moment keep the
            order they were saved in, the later one first.
        """
        ...

    def list_saved_since(self, earliest: datetime) -> tuple[SavedTake5, ...]:
        """Get the Take 5s saved at or after a moment, the newest first.

        Args:
            earliest: The moment, in any time zone.

        Returns:
            The saved Take 5s, newest first.
        """
        ...

    def fixed_among(self, take5_ids: Collection[UUID]) -> frozenset[UUID]:
        """Find which of these Take 5s a saved Take 5 fixes.

        Args:
            take5_ids: The IDs to look for.

        Returns:
            The ones some saved Take 5 points back at with `fixes`.
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


class HazardJudge(Protocol):
    """Anything that judges whether a hazard is vague: an AI, or a stand-in in tests."""

    def judge(self, hazard_text: str) -> str:
        """Say whether one hazard is vague or specific (spec T6).

        Args:
            hazard_text: The hazard as `hazard_judgement_text()` writes it out. It never
                holds the worker's name.

        Returns:
            The reply, one word of "specific", "vague", "stock" or "unfit", which the
            service checks before it is used (decisions D58, D105).
        """
        ...


class Take5Ranker(Protocol):
    """Anything that ranks the worst Take 5s and picks the best: an AI or a stand-in."""

    def rank(self, take5s_text: str) -> str:
        """Order the worst Take 5s and write one line on each (spec W6).

        Args:
            take5s_text: The Take 5s as `ranking_text()` writes them out. It never
                holds a worker's name.

        Returns:
            The reply, unchecked; `checked_ai_order()` decides whether it is used.
        """
        ...

    def pick_best(self, take5s_text: str) -> str:
        """Pick the best of the careful Take 5s and say what was good (spec W8).

        Args:
            take5s_text: The Take 5s as `best_text()` writes them out. It never holds
                a worker's name.

        Returns:
            The reply, unchecked; `checked_ai_pick()` decides whether it is used.
        """
        ...
