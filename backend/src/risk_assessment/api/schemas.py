"""The shapes of the API's requests and responses, including its error replies."""

from datetime import datetime
from typing import ClassVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from risk_assessment.domain.controls import ControlKind
from risk_assessment.domain.questions import Answer, Question
from risk_assessment.domain.risk import RiskMatrix, RiskRating
from risk_assessment.domain.take5.draft import FieldError, Take5Draft
from risk_assessment.domain.take5.saved import SavedTake5
from risk_assessment.domain.take5.template import LevelGuidance


class TemplateResponse(BaseModel):
    """The card a new Take 5 is filled in on, so the phone keeps no copy of it.

    Attributes:
        name: The template's name.
        questions: The card's questions, in the order it prints them, each with its
            role.
        answer_choices: The answers a question can have, in the order to show them.
        matrix: The risk matrix the hazards are rated on.
        control_kinds: Every kind of control, strongest first.
        likelihood_guidance: What each likelihood means, in the card's words.
        consequence_guidance: What each consequence means, in the card's words.
        control_guidance: The card's advice on choosing controls.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    name: str
    questions: tuple[Question, ...]
    answer_choices: tuple[Answer, ...]
    matrix: RiskMatrix
    control_kinds: tuple[ControlKind, ...]
    likelihood_guidance: tuple[LevelGuidance, ...]
    consequence_guidance: tuple[LevelGuidance, ...]
    control_guidance: str


class SubmissionRequest(BaseModel):
    """A Take 5 to save, with an ID the phone made so a retry can't save it twice.

    Attributes:
        id: Made once by the phone and sent again, unchanged, on every retry.
        draft: The worker's answers.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    id: UUID
    draft: Take5Draft


class Take5Response(BaseModel):
    """A saved Take 5, with the overall rating the back end worked out for it.

    Attributes:
        take5: The saved Take 5, with its verdict and a copy of its template.
        rating: The Take 5's rating (spec R4 and R5).
        fixed_by: The ID of the newest Take 5 that fixes this one, or None. It is
            found when the Take 5 is opened, because the saved one never changes.
        offers_fix: True when the result should offer to fix this Take 5 in a new
            one: it said Don't start yet and has no fix yet.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    take5: SavedTake5
    rating: RiskRating
    fixed_by: UUID | None
    offers_fix: bool


class Take5Summary(BaseModel):
    """One line of the saved Take 5 list: enough to find it, not the whole card.

    Attributes:
        id: The Take 5's ID, to open it.
        created_at: When it was saved.
        worker_name: Who did it.
        job: What the job is.
        can_start: The verdict it was saved with: True for Good to go, False for
            Don't start yet.
        fixed: True when a newer Take 5 fixes this one.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    id: UUID
    created_at: datetime
    worker_name: str
    job: str
    can_start: bool
    fixed: bool


class ErrorMessage(BaseModel):
    """The reply for a 404 or a 409: one message a person can read.

    Attributes:
        detail: What went wrong, in plain words.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    detail: str


class FormErrors(BaseModel):
    """The reply for every 422: what is missing or wrong, field by field.

    Attributes:
        detail: A summary for the top of the screen.
        errors: Each problem, with the dotted path of the field it belongs beside.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    detail: str
    errors: tuple[FieldError, ...]
