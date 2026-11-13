"""The card's kinds of control, shared by any kind of risk assessment."""

from enum import StrEnum
from typing import ClassVar

from pydantic import BaseModel, ConfigDict


class ControlKind(StrEnum):
    """The card's six controls, ordered from strongest to weakest."""

    REMOVE = "Remove the hazard"
    ISOLATE = "Isolate the hazard"
    BARRICADE = "Barricade the hazard"
    SYSTEMS = "Put systems in place (permits, safe work procedures)"
    BEHAVIOUR = "Ensure correct behaviour"
    PPE = "Wear PPE"

    @property
    def is_strong(self) -> bool:
        """Say whether the control works without relying on people's behaviour."""
        return self in (ControlKind.REMOVE, ControlKind.ISOLATE, ControlKind.BARRICADE)


class Control(BaseModel):
    """What the worker will do about a hazard, and what kind of control it is."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    description: str
    kind: ControlKind
