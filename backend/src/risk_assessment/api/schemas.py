"""The shapes of the API's requests and responses, including its error replies."""

from datetime import datetime
from typing import ClassVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from risk_assessment.domain.controls import ControlKind
from risk_assessment.domain.questions import Answer, Question
from risk_assessment.domain.risk import RiskMatrix, RiskRating
from risk_assessment.domain.take5.areas import AreaRisk
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
        ai_notice: What Submit sends to the AI, to show above Submit, or None when
            no AI is set up, so nothing is sent (decision D52).
        hazard_ai_notice: That hazards linked to a Yes are checked by an AI, to show
            on the hazard check page, or None when the word rule judges them, so
            nothing is sent (decision D63).
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
    ai_notice: str | None = None
    hazard_ai_notice: str | None = None


class SubmissionRequest(BaseModel):
    """A Take 5 to save, with an ID the phone made so a retry can't save it twice.

    Attributes:
        id: Made once by the phone and sent again, unchanged, on every retry.
        draft: The worker's answers.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    id: UUID
    draft: Take5Draft


class PaperTake5Request(BaseModel):
    """A checked paper card to save as written (spec P1, P5, task 0033).

    Attributes:
        id: Made once by the page and sent again, unchanged, on every retry.
        draft: The card as the person checked it, with the worker's name as written.
        filled_in_at: The card's date, "YYYY-MM-DD" or "YYYY-MM-DDTHH:MM", as read
            and checked, or None when it has none.
        time_zone: The checker's time zone, such as "Australia/Perth", for the date.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    id: UUID
    draft: Take5Draft
    filled_in_at: str | None = None
    time_zone: str


class BatchRankingRequest(BaseModel):
    """Saved Take 5s to rank on their own, such as a batch of scanned cards (F10).

    Attributes:
        ids: The Take 5s' IDs, at most 200.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    ids: tuple[UUID, ...] = Field(max_length=200)


class AnswerRequest(BaseModel):
    """The worker's answer to a Take 5's challenge question.

    Attributes:
        answer: What the worker wrote.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    answer: str


class Take5Response(BaseModel):
    """A saved Take 5, with the overall rating the back end worked out for it.

    Attributes:
        take5: The saved Take 5, with its question and a copy of its template. Its
            verdict is empty until the question is answered.
        rating: The Take 5's rating (spec R4 and R5), or None for a paper card with
            no rated hazard (P2).
        fixed_by: The ID of the newest Take 5 that fixes this one, or None. It is
            found when the Take 5 is opened, because the saved one never changes.
        offers_fix: True when the result should offer to fix this Take 5 in a new
            one: it said Don't start yet and has no fix yet.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    take5: SavedTake5
    rating: RiskRating | None
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
            Don't start yet, or None while its question is unanswered.
        fixed: True when a newer Take 5 fixes this one.
        from_paper: True when it was photographed off a paper card (P6).
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    id: UUID
    created_at: datetime
    worker_name: str
    job: str
    can_start: bool | None
    fixed: bool
    from_paper: bool


class Take5ListPage(BaseModel):
    """One page of the saved Take 5 list, the newest first (spec D18 and D80).

    Attributes:
        take5s: Up to 50 lines of the list.
        next: The ID to send as `before` for the next page, or None when there are no
            more.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    take5s: tuple[Take5Summary, ...]
    next: UUID | None


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


class RankedTake5Line(BaseModel):
    """One Take 5 in a ranking, worst first, with why it sits there (spec W1 to W7).

    Attributes:
        id: The Take 5's ID, to open it.
        created_at: When it was saved.
        worker_name: Who did it (decided by Jake, 2026-11-19). Never sent to the AI.
        job: What the job is.
        can_start: The verdict it was saved with: True for Good to go, False for
            Don't start yet, or None while its question is unanswered.
        line: One line saying why it sits where it does.
        ranked_by_ai: True when the AI placed it and wrote the line, False when the
            fixed rules did.
        from_paper: True when it was photographed off a paper card (P6).
        started_at: When it was started: for a paper card, the date on the card,
            at midnight where the checker was when it has no time (P5). None when
            not known.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    id: UUID
    created_at: datetime
    worker_name: str
    job: str
    can_start: bool | None
    line: str
    ranked_by_ai: bool
    from_paper: bool
    started_at: datetime | None


class BestTake5Line(BaseModel):
    """The best careful Take 5 of the set, with what was good about it (spec W8).

    Attributes:
        id: The Take 5's ID, to open it.
        created_at: When it was saved.
        worker_name: Who did it. Never sent to the AI.
        job: What the job is.
        can_start: The verdict it was saved with: True for Good to go, False for
            Don't start yet.
        line: One line saying what was good about it.
        picked_by_ai: True when the AI picked it and wrote the line, False when the
            fixed rules did.
        minutes_taken: How many minutes it took, or None when that can't be told.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    id: UUID
    created_at: datetime
    worker_name: str
    job: str
    can_start: bool
    line: str
    picked_by_ai: bool
    minutes_taken: int | None


class RankedTake5s(BaseModel):
    """Every Take 5 started since a moment worst first, and the best (W7 to W9, D92).

    Attributes:
        take5s: The ranking. The page shows the first 5, then the rest on request.
        best: The best careful one, or None when none is careful.
        typical_minutes: The median minutes a finished one took, or None.
        today_only: True when only today's are ranked; False when every saved Take 5
            is, as `TAKE5_RANK_TODAY_ONLY` sets (D118).
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    take5s: tuple[RankedTake5Line, ...]
    best: BestTake5Line | None
    typical_minutes: int | None
    today_only: bool


class RiskByArea(BaseModel):
    """Every area with a Take 5 in the time counted, hottest first (A1 to A5).

    Attributes:
        areas: Each area and what its Take 5s show, hottest first.
        last_30_days_only: True when only the last 30 days count; False when every
            saved Take 5 does, as `TAKE5_AREA_LAST_30_DAYS_ONLY` sets (D119).
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    areas: tuple[AreaRisk, ...]
    last_30_days_only: bool


class ScannedCardResponse(BaseModel):
    """A paper card as the AI read it, for a person to check (task 0033).

    Nothing is saved yet: the page keeps the card until the person has checked it.

    Attributes:
        draft: The card as a draft Take 5, with the worker's name as written.
        filled_in_at: The date, or date and time, written on the card, as
            "YYYY-MM-DD" or "YYYY-MM-DDTHH:MM" with no time zone; None when there was
            none or it couldn't be read.
        unreadable: The dotted paths of fields left empty because the AI couldn't read
            them, such as "job" or "hazards.0.before.likelihood".
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    draft: Take5Draft
    filled_in_at: str | None
    unreadable: tuple[str, ...]
