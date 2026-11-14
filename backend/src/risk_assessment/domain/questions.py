"""Yes / No / N/A questions, shared by any kind of risk assessment.

A question's role says what its answer means, so the rules never need to know a
question's wording. Another company's card is then different data, not different code.
"""

from enum import StrEnum
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field


class QuestionRole(StrEnum):
    """What a question's answer means for the job."""

    STOP = "stop"
    """No means don't start until it is sorted."""

    HAZARD = "hazard"
    """Yes means there is a hazard to list and control."""


class Answer(StrEnum):
    """The three answers a question can have. Nothing is picked to begin with."""

    YES = "Yes"
    NO = "No"
    NOT_APPLICABLE = "N/A"


class Question(BaseModel):
    """One question on a card.

    Attributes:
        id: A short name that stays the same if the wording is tidied, such as
            `permits`. Answers are kept against it. Lower-case letters, digits and
            underscores only, so it is safe in a dotted path like `answers.permits`.
        text: The question as the card prints it.
        role: What its answer means for the job.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    id: str = Field(pattern=r"^[a-z0-9_]+$")
    text: str
    role: QuestionRole
