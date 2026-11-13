"""The storage interface required by the Take 5 service."""

from typing import Protocol
from uuid import UUID

from risk_assessment.domain.take5.saved import SavedTake5


class Take5Repository(Protocol):
    """Store immutable documents; an existing ID always keeps its first document."""

    def add(self, take5: SavedTake5) -> SavedTake5:
        """Insert once and return the document held for this ID."""
        ...

    def get(self, take5_id: UUID) -> SavedTake5 | None:
        """Return one document, or nothing when the ID is unknown."""
        ...
