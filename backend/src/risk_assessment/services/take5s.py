"""Check, nudge, submit, answer, get and list Take 5s, with swappable storage and AI."""

import logging
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from typing import Any, ClassVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from risk_assessment.domain.take5.challenge import (
    AI_TIME_LIMIT_SECONDS,
    Challenge,
    ai_challenge,
    answer_error,
    challenge_text,
    fallback_challenge,
)
from risk_assessment.domain.take5.draft import (
    DraftCheck,
    FieldError,
    Take5Draft,
    check_draft,
)
from risk_assessment.domain.take5.fix import fixes_error
from risk_assessment.domain.take5.hazard_nudges import (
    HAZARD_AI_TIME_LIMIT_SECONDS,
    Nudge,
    with_kept_flags,
)
from risk_assessment.domain.take5.saved import SavedTake5
from risk_assessment.domain.take5.take5 import Hazard
from risk_assessment.domain.take5.template import Take5Template
from risk_assessment.domain.take5.time_limit import runs_out_at, time_limit_error
from risk_assessment.domain.take5.verdict import verdict
from risk_assessment.services.hazard_nudges import HazardNudger
from risk_assessment.services.ports import ChallengeAsker, HazardJudge, Take5Repository

_logger: logging.Logger = logging.getLogger(__name__)

# How many saved Take 5s the list shows at a time (spec D18 and D82).
SAVED_LIST_PAGE_SIZE: int = 50

# The fields that differ between two saves of the same answers.
_SAVE_DETAILS: dict[str, Any] = {
    "id": True,
    "created_at": True,
    "finished_at": True,
    "verdict": True,
    "challenge": True,
    # What the hazard check flagged depends on the AI at the time, not the worker.
    "hazards": {"__all__": {"kept_flag"}},
}


class SavedListPage(BaseModel):
    """One page of the saved list, newest first.

    Attributes:
        take5s: Up to `SAVED_LIST_PAGE_SIZE` saved Take 5s, newest first.
        fixed_ids: Which of them a newer Take 5 fixes, wherever that fix is listed.
        next_older_than: The last one's ID, to ask for the page after it, or None
            when there are no more.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    take5s: tuple[SavedTake5, ...]
    fixed_ids: frozenset[UUID]
    next_older_than: UUID | None


class InvalidDraftError(ValueError):
    """A draft that can't be submitted yet, with what is missing.

    Attributes:
        check: The failed check, with each field's error.
    """

    def __init__(self, check: DraftCheck) -> None:
        """Keep the failed check so the API can send each field's error.

        Args:
            check: The failed check.
        """
        super().__init__("Fill in the highlighted fields before you submit.")
        self.check: DraftCheck = check


class SubmissionConflictError(ValueError):
    """The submission ID was already used to save different answers."""


class Take5NotFoundError(LookupError):
    """No Take 5 is saved with this ID."""


class InvalidAnswerError(ValueError):
    """An answer to the challenge question that can't be accepted yet (spec C4).

    Attributes:
        error: What is wrong, to show beside the answer.
    """

    def __init__(self, error: FieldError) -> None:
        """Keep the error so the API can send it beside the answer.

        Args:
            error: What is wrong with the answer.
        """
        super().__init__("Answer the question before you finish.")
        self.error: FieldError = error


class AlreadyAnsweredError(ValueError):
    """A different answer to a Take 5 that is already finished (spec C6)."""


def utc_now() -> datetime:
    """Return the time now, in UTC: the clock the service uses unless a test swaps it.

    Returns:
        The time now.
    """
    return datetime.now(UTC)


class Take5Service:
    """Apply the rules once, then keep the exact result the worker was shown."""

    def __init__(
        self,
        repository: Take5Repository,
        template: Take5Template,
        clock: Callable[[], datetime] = utc_now,
        challenge_asker: ChallengeAsker | None = None,
        ai_time_limit_seconds: float = AI_TIME_LIMIT_SECONDS,
        hazard_judge: HazardJudge | None = None,
        hazard_ai_time_limit_seconds: float = HAZARD_AI_TIME_LIMIT_SECONDS,
    ) -> None:
        """Take the storage, the template, a clock and the AI from the composition root.

        Args:
            repository: Where Take 5s are kept.
            template: The template new Take 5s are filled in on.
            clock: Says what time it is now. Tests pass a fixed one.
            challenge_asker: The AI that writes the challenge question, or None when
                none is set up, which asks the fixed question every time (spec C3).
            ai_time_limit_seconds: How long to wait for the AI before asking the fixed
                question instead. 10 seconds (spec C3); tests pass a shorter time.
            hazard_judge: The AI that judges whether a hazard is vague, or None when
                none is set up, so the word rule always decides (spec T6).
            hazard_ai_time_limit_seconds: How long to wait for that AI before the word
                rule decides. 5 seconds (decision D57); tests pass a shorter time.
        """
        self._repository: Take5Repository = repository
        self._template: Take5Template = template
        self._clock: Callable[[], datetime] = clock
        self._challenge_asker: ChallengeAsker | None = challenge_asker
        self._ai_time_limit_seconds: float = ai_time_limit_seconds
        self._hazard_nudger: HazardNudger = HazardNudger(
            template,
            hazard_judge,
            hazard_ai_time_limit_seconds,
        )

    @property
    def template(self) -> Take5Template:
        """The template a new Take 5 is filled in on."""
        return self._template

    @property
    def asks_ai(self) -> bool:
        """Whether an AI writes the challenge question, not always the fallback."""
        return self._challenge_asker is not None

    @property
    def judges_hazards_with_ai(self) -> bool:
        """Whether an AI judges vague hazards, not always the word rule (spec T6)."""
        return self._hazard_nudger.asks_ai

    def check(self, draft: Take5Draft) -> DraftCheck:
        """Check a draft against the current template, without saving it.

        Args:
            draft: The worker's answers so far.

        Returns:
            What is missing, the warnings, and the rated Take 5 when nothing is
            missing, and when the draft runs out. A draft older than the template's
            time limit has an error on `started_at` (spec K2).
        """
        time_limit_minutes: int | None = self._template.draft_time_limit_minutes
        check: DraftCheck = _with_error(
            check_draft(draft, self._template),
            time_limit_error(draft.started_at, self._clock(), time_limit_minutes),
        )
        return check.model_copy(
            update={"runs_out_at": runs_out_at(draft.started_at, time_limit_minutes)},
        )

    def nudges(self, draft: Take5Draft) -> tuple[Nudge, ...]:
        """Nudge each vague hazard linked to a Yes to say what could hurt and where.

        Args:
            draft: The worker's answers so far. Nothing is saved.

        Returns:
            One nudge for each vague hazard, judged by the AI when it answers in time
            and by the word rule otherwise (spec T6).
        """
        return self._hazard_nudger.nudges(draft)

    def submit(self, draft: Take5Draft, submission_id: UUID) -> SavedTake5:
        """Check and save a Take 5 once, then ask its question. A retry gets the same.

        The Take 5 is saved before the AI is asked, so a slow or failed AI never loses
        it (spec F2). It stays unfinished, with no verdict, until the question is
        answered (spec C6).

        Args:
            draft: The worker's answers.
            submission_id: The ID the phone made for this Take 5. It is the same on
                every retry.

        Returns:
            The saved Take 5, with its question: unfinished, unless a retry finds it
            already answered.

        Raises:
            InvalidDraftError: If anything is missing, `draft.fixes` isn't a saved
                Don't start yet, or the draft has run out (spec K2). A retry of a
                Take 5 that was saved in time is never refused for running out.
            SubmissionConflictError: If the ID was already used for other answers.
        """
        previous: SavedTake5 | None = self._repository.get(submission_id)
        template: Take5Template = (
            previous.template if previous is not None else self._template
        )
        now: datetime = self._clock()
        check: DraftCheck = _with_error(
            check_draft(draft, template),
            self._fixes_error(draft.fixes, submission_id),
        )
        if previous is None:
            check = _with_error(
                check,
                time_limit_error(
                    draft.started_at,
                    now,
                    template.draft_time_limit_minutes,
                ),
            )
        if check.assessment is None:
            raise InvalidDraftError(check)
        # A retry finds the first save, so the hazards are checked only the first time,
        # and what was flagged is left out when the two are compared. Only verdicts
        # the AI already gave are used, so kept words are never sent again (D37).
        hazards: tuple[Hazard, ...] = (
            check.assessment.hazards
            if previous is not None
            else with_kept_flags(
                check.assessment.hazards,
                self._hazard_nudger.nudges(draft, ask_ai=False),
            )
        )
        submitted = SavedTake5(
            template=template,
            answers=check.assessment.answers,
            hazards=hazards,
            id=submission_id,
            created_at=now,
            worker_name=draft.worker_name.strip(),
            job=draft.job.strip(),
            location=draft.location.strip(),
            fixes=draft.fixes,
            started_at=draft.started_at,
        )
        saved: SavedTake5 = (
            previous if previous is not None else self._repository.add(submitted)
        )
        if _answers(saved) != _answers(submitted):
            raise SubmissionConflictError(
                "This Take 5 was already saved with different answers.",
            )
        return self._with_question(saved, ask_ai=True)

    def answer(self, take5_id: UUID, answer: str) -> SavedTake5:
        """Save the answer to a Take 5's question, and finish it with its verdict.

        The verdict is worked out from what was saved, on the template it was saved
        with, so the answer never changes it (spec C5). The same answer sent again,
        such as a retry after a lost reply, gets back the finished Take 5.

        Args:
            take5_id: The Take 5's ID.
            answer: The worker's answer.

        Returns:
            The finished Take 5, with its verdict.

        Raises:
            Take5NotFoundError: If no Take 5 is saved with this ID.
            InvalidAnswerError: If the answer is shorter than four words (spec C4).
            AlreadyAnsweredError: If the Take 5 was already finished with another
                answer, or before it had a question (spec C6).
        """
        saved: SavedTake5 | None = self.get(take5_id)
        if saved is None:
            raise Take5NotFoundError("This Take 5 could not be found.")
        answer = answer.strip()
        if saved.is_finished:
            return _answered_with(saved, answer)
        error: FieldError | None = answer_error(answer)
        if error is not None:
            raise InvalidAnswerError(error)
        challenge: Challenge = saved.challenge or fallback_challenge(saved)
        finished: SavedTake5 = saved.model_copy(
            update={
                "challenge": challenge.model_copy(update={"answer": answer}),
                "verdict": verdict(saved),
                "finished_at": self._clock(),
            },
        )
        return _answered_with(self._repository.finish(finished), answer)

    def get(self, take5_id: UUID) -> SavedTake5 | None:
        """Get a saved Take 5 as it was saved, without applying today's rules.

        An unfinished Take 5 with no question (the app stopped between saving it and
        asking) is given the fixed question, so opening it always shows one (spec C6).

        Args:
            take5_id: The Take 5's ID.

        Returns:
            The saved Take 5, or None if there is none with this ID.
        """
        saved: SavedTake5 | None = self._repository.get(take5_id)
        return self._with_question(saved, ask_ai=False) if saved is not None else None

    def saved_list_page(self, older_than: UUID | None = None) -> SavedListPage:
        """Get one page of saved Take 5s as they were saved, the newest first.

        Everyone using the app sees the same list (spec decision D8). One more than a
        page is read, only to learn whether another page follows.

        Args:
            older_than: The last Take 5 already shown, or None for the first page.

        Returns:
            The page, which of its Take 5s are fixed, and where the next page starts.
        """
        read: tuple[SavedTake5, ...] = self._repository.list_newest_first(
            older_than,
            SAVED_LIST_PAGE_SIZE + 1,
        )
        shown: tuple[SavedTake5, ...] = read[:SAVED_LIST_PAGE_SIZE]
        more_follow: bool = len(read) > SAVED_LIST_PAGE_SIZE
        return SavedListPage(
            take5s=shown,
            fixed_ids=self._repository.fixed_among([take5.id for take5 in shown]),
            next_older_than=shown[-1].id if more_follow else None,
        )

    def fixed_by(self, take5_id: UUID) -> UUID | None:
        """Find the newest saved Take 5 that fixes this one.

        Args:
            take5_id: The ID of the Take 5 that may have been fixed.

        Returns:
            The fix's ID, or None if it hasn't been fixed.
        """
        return self._repository.fixed_by(take5_id)

    def _with_question(self, saved: SavedTake5, ask_ai: bool) -> SavedTake5:
        """Give an unfinished Take 5 its question, once.

        Args:
            saved: The saved Take 5.
            ask_ai: Whether to ask the AI first. When False, or when the AI can't
                give a usable question, the fixed question is asked (spec C3).

        Returns:
            The Take 5 as now saved. One that is finished, or already has its
            question, comes back unchanged.
        """
        if saved.is_finished or saved.challenge is not None:
            return saved
        challenge: Challenge = (
            self._ai_challenge(saved) if ask_ai else None
        ) or fallback_challenge(saved)
        return self._repository.save_question(
            saved.model_copy(update={"challenge": challenge}),
        )

    def _ai_challenge(self, saved: SavedTake5) -> Challenge | None:
        """Ask the AI for the question, giving up after the time limit.

        The worker never sees an AI error: any failure is logged and the caller asks
        the fixed question instead.

        Args:
            saved: The saved Take 5. Only its job, location, answers and hazards are
                sent, never the worker's name (spec C1).

        Returns:
            The AI's question, or None when no AI is set up, it fails, it takes longer
            than the time limit, or its reply fails C2.
        """
        if self._challenge_asker is None:
            return None
        take5_text: str = challenge_text(saved, saved.job, saved.location)
        # Not a `with` block: leaving one waits for the AI, even after the time limit.
        executor = ThreadPoolExecutor(max_workers=1)
        try:
            reply = executor.submit(self._challenge_asker.ask, take5_text)
            return ai_challenge(reply.result(timeout=self._ai_time_limit_seconds))
        except Exception:  # Any AI failure at all means the fixed question.
            _logger.warning(
                "The AI could not ask a question, so the fixed one was asked.",
                exc_info=True,
            )
            return None
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

    def _fixes_error(
        self,
        fixes: UUID | None,
        submission_id: UUID,
    ) -> FieldError | None:
        """Say why the draft can't fix the Take 5 it says it fixes, if it can't.

        Args:
            fixes: The ID of the Take 5 the draft says it fixes, or None.
            submission_id: The draft's own ID. A Take 5 can't fix itself.

        Returns:
            The error, or None when the draft fixes nothing or may fix that Take 5.
        """
        if fixes is None:
            return None
        fixed: SavedTake5 | None = (
            None if fixes == submission_id else self._repository.get(fixes)
        )
        return fixes_error(fixed)


def _with_error(check: DraftCheck, error: FieldError | None) -> DraftCheck:
    """Add one more error to a check, which then has nothing to submit.

    Args:
        check: The draft's check so far.
        error: The error to add, or None to leave the check as it is.

    Returns:
        The check, with the error added if there is one.
    """
    if error is None:
        return check
    return check.model_copy(
        update={
            "errors": (*check.errors, error),
            "assessment": None,
            "can_submit": False,
        },
    )


def _answered_with(saved: SavedTake5, answer: str) -> SavedTake5:
    """Return a finished Take 5 if it was finished with this answer.

    Args:
        saved: A finished Take 5.
        answer: The answer just sent, without spaces at its ends.

    Returns:
        The finished Take 5, when its saved answer is this one.

    Raises:
        AlreadyAnsweredError: If it was finished with another answer, or before it had
            a question.
    """
    if saved.challenge is None or saved.challenge.answer != answer:
        raise AlreadyAnsweredError(
            "This Take 5 is already finished, so it can't be answered again.",
        )
    return saved


def _answers(take5: SavedTake5) -> dict[str, Any]:
    """Return what the worker gave and what it was filled in on, without save details.

    Args:
        take5: A saved Take 5.

    Returns:
        Its fields, without the ID, the times, the verdict, the question and what the
        hazard check flagged.
    """
    return take5.model_dump(exclude=_SAVE_DETAILS)
