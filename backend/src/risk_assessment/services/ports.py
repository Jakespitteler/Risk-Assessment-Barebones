"""The storage interface required by the Take 5 service."""

from typing import Protocol
from uuid import UUID

from risk_assessment.domain.take5.saved import SavedTake5


class Take5Repository(Protocol):
    """Where Take 5s are kept. A saved Take 5 is never replaced or changed."""

    def add(self, take5: SavedTake5) -> SavedTake5:
        """Save a Take 5, unless one with the same ID is already saved.

        Args:
            take5: The Take 5 to save.

        Returns:
            The Take 5 now saved with this ID: this one, or the one saved first.
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

    def fixed_by(self, take5_id: UUID) -> UUID | None:
        """Find the newest saved Take 5 whose `fixes` is this ID.

        Args:
            take5_id: The ID of the Take 5 that may have been fixed.

        Returns:
            The newest fix's ID, or None if there is none.
        """
        ...
