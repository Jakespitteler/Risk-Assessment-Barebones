"""Judge the hazards linked to a Yes, with an AI when one is set up (spec T6).

The AI has a few seconds to judge each hazard. Whatever it hasn't judged by then, the
word rule decides, so the worker never waits long and never sees an AI error. Each
usable verdict is remembered for the exact text the AI was given, so the same words
are never paid for twice while the server runs (decision D59).
"""

import logging
from collections import OrderedDict
from concurrent.futures import Future, ThreadPoolExecutor, wait
from threading import Lock

from risk_assessment.domain.take5.draft import Take5Draft
from risk_assessment.domain.take5.hazard_nudges import (
    HAZARD_AI_TIME_LIMIT_SECONDS,
    HazardVerdict,
    Nudge,
    hazard_judgement_text,
    hazard_verdict,
    hazards_to_judge,
    specific_hazard_nudges,
)
from risk_assessment.domain.take5.take5 import HazardFlag
from risk_assessment.domain.take5.template import Take5Template
from risk_assessment.services.ai_failures import (
    ai_failure_kind,
    is_expected_ai_failure,
)
from risk_assessment.services.ports import HazardJudge

_logger: logging.Logger = logging.getLogger(__name__)

# Far more than a crew writes in a day. Past it, the oldest verdicts are forgotten.
REMEMBERED_VERDICTS_LIMIT: int = 1000
# How many hazards can be with the AI at once. Any more wait their turn.
AI_CALLS_AT_ONCE: int = 16


class RememberedVerdicts:
    """The AI's verdicts, by the exact text it was given, until the server restarts.

    Safe to use from several threads at once, as the AI is asked in background threads.
    """

    def __init__(self, limit: int = REMEMBERED_VERDICTS_LIMIT) -> None:
        """Start with nothing remembered.

        Args:
            limit: The most verdicts kept. Past it, the oldest is forgotten first.
        """
        self._limit: int = limit
        self._verdicts: OrderedDict[str, HazardVerdict] = OrderedDict()
        self._lock: Lock = Lock()

    def get(self, hazard_text: str) -> HazardVerdict | None:
        """Look up the verdict on this exact text.

        Args:
            hazard_text: The text the AI was given.

        Returns:
            The verdict, or None when the AI hasn't judged this text.
        """
        with self._lock:
            return self._verdicts.get(hazard_text)

    def remember(self, hazard_text: str, verdict: HazardVerdict) -> None:
        """Keep a verdict, forgetting the oldest one if there are too many.

        Args:
            hazard_text: The text the AI was given.
            verdict: What it decided.
        """
        with self._lock:
            self._verdicts[hazard_text] = verdict
            self._verdicts.move_to_end(hazard_text)
            while len(self._verdicts) > self._limit:
                self._verdicts.popitem(last=False)


class RememberedFlags:
    """The flag last shown on each hazard's words, until the server restarts.

    Safe to use from several threads at once.
    """

    def __init__(self, limit: int = REMEMBERED_VERDICTS_LIMIT) -> None:
        """Start with nothing remembered.

        Args:
            limit: The most flags kept. Past it, the oldest is forgotten first.
        """
        self._limit: int = limit
        self._flags: OrderedDict[str, HazardFlag] = OrderedDict()
        self._lock: Lock = Lock()

    def get(self, hazard_text: str) -> HazardFlag | None:
        """Look up the flag last shown on this exact text.

        Args:
            hazard_text: What the AI would be given about the hazard.

        Returns:
            The flag, or None when none was shown on this text.
        """
        with self._lock:
            return self._flags.get(hazard_text)

    def remember(self, hazard_text: str, flag: HazardFlag) -> None:
        """Note a flag shown, forgetting the oldest one if there are too many.

        Args:
            hazard_text: What the AI would be given about the hazard.
            flag: The flag the worker was shown.
        """
        with self._lock:
            self._flags[hazard_text] = flag
            self._flags.move_to_end(hazard_text)
            while len(self._flags) > self._limit:
                self._flags.popitem(last=False)


def _shown_key(texts: dict[int, str], nudge: Nudge) -> str:
    """Find the judgement text of the hazard a nudge is on.

    Args:
        texts: The text for each judged hazard, by its place on the list.
        nudge: A nudge on one of them, at `hazards.<index>.description`.

    Returns:
        That hazard's text.
    """
    return texts[int(nudge.path.split(".")[1])]


class HazardNudger:
    """Nudge each vague, stock or unfit hazard linked to a Yes (T6, T7).

    An AI judges when one is set up; the word rule decides otherwise.
    """

    def __init__(
        self,
        template: Take5Template,
        judge: HazardJudge | None = None,
        time_limit_seconds: float = HAZARD_AI_TIME_LIMIT_SECONDS,
    ) -> None:
        """Take the template and the AI from the composition root.

        Args:
            template: The template drafts are filled in on.
            judge: The AI that judges hazards, or None when none is set up, so the
                word rule always decides.
            time_limit_seconds: How long to wait for the AI before the word rule
                decides. 5 seconds (decision D57); tests pass a shorter time.
        """
        self._template: Take5Template = template
        self._judge: HazardJudge | None = judge
        self._time_limit_seconds: float = time_limit_seconds
        self._remembered: RememberedVerdicts = RememberedVerdicts()
        # The flag last shown on each hazard's words, so a submit counts only what
        # the worker saw (task 0037). The word rule's flags are noted here too.
        self._shown: RememberedFlags = RememberedFlags()
        # Hazards with the AI now, so a second check of the same words waits for the
        # same answer instead of paying for another.
        self._asking: dict[str, Future[HazardVerdict | None]] = {}
        self._asking_lock: Lock = Lock()
        # Kept for the server's life: it is only made when there is an AI to ask.
        self._executor: ThreadPoolExecutor | None = (
            None if judge is None else ThreadPoolExecutor(max_workers=AI_CALLS_AT_ONCE)
        )

    @property
    def asks_ai(self) -> bool:
        """Whether an AI judges hazards, not always the word rule."""
        return self._judge is not None

    def nudges(self, draft: Take5Draft) -> tuple[Nudge, ...]:
        """Find every flagged hazard linked to a Yes, and say what to do about it.

        Each nudge returned is noted as shown, so submitting can tell which flags the
        worker saw and kept (task 0037).

        Args:
            draft: The worker's answers so far. The worker's name is never sent to the
                AI: only each hazard, its question, the job and the location are.

        Returns:
            One nudge for each vague, stock or unfit hazard, in the order of the list.
        """
        texts: dict[int, str] = self._judgement_texts(draft)
        verdicts: dict[str, HazardVerdict] = self._ai_verdicts(
            frozenset(texts.values()),
        )
        nudges: tuple[Nudge, ...] = self._nudges_from(draft, texts, verdicts)
        for nudge in nudges:
            self._shown.remember(_shown_key(texts, nudge), nudge.flag)
        return nudges

    def kept_nudges(self, draft: Take5Draft) -> tuple[Nudge, ...]:
        """Find the nudges the worker was shown and kept, asking the AI nothing new.

        Words the worker kept are never sent again (D37), so only the AI's remembered
        verdicts and the word rule decide. A nudge counts only when the worker was
        shown the same flag on the same words: a verdict that came too late to show,
        or a hazard never checked, is never saved as kept.

        Args:
            draft: The worker's answers, as submitted.

        Returns:
            Each nudge still on the draft that the worker saw, in the order of the list.
        """
        texts: dict[int, str] = self._judgement_texts(draft)
        verdicts: dict[str, HazardVerdict] = self._remembered_verdicts(
            frozenset(texts.values()),
        )
        return tuple(
            nudge
            for nudge in self._nudges_from(draft, texts, verdicts)
            if self._shown.get(_shown_key(texts, nudge)) is nudge.flag
        )

    def _judgement_texts(self, draft: Take5Draft) -> dict[int, str]:
        """Write what the AI would be given about each hazard T6 judges.

        Args:
            draft: The worker's answers so far.

        Returns:
            The text for each judged hazard, by its place on the list.
        """
        return {
            hazard.index: hazard_judgement_text(hazard, draft.job, draft.location)
            for hazard in hazards_to_judge(draft, self._template)
        }

    def _nudges_from(
        self,
        draft: Take5Draft,
        texts: dict[int, str],
        verdicts: dict[str, HazardVerdict],
    ) -> tuple[Nudge, ...]:
        """Nudge each flagged hazard, by the AI's verdict where there is one.

        Args:
            draft: The worker's answers so far.
            texts: The text for each judged hazard, by its place on the list.
            verdicts: The AI's verdict on each text it judged.

        Returns:
            One nudge for each flagged hazard, in the order of the list.
        """
        return specific_hazard_nudges(
            draft,
            self._template,
            {
                index: verdicts[text]
                for index, text in texts.items()
                if text in verdicts
            },
        )

    def _remembered_verdicts(
        self,
        texts: frozenset[str],
    ) -> dict[str, HazardVerdict]:
        """Get the AI's remembered verdict on each text, asking it nothing new.

        Args:
            texts: What the AI would be given about each hazard.

        Returns:
            The verdict on each text the AI has already judged.
        """
        return {
            text: verdict
            for text in texts
            if (verdict := self._remembered.get(text)) is not None
        }

    def _ai_verdicts(self, texts: frozenset[str]) -> dict[str, HazardVerdict]:
        """Get the AI's verdict on each text: remembered, or asked for now.

        Args:
            texts: What the AI is given about each hazard to judge.

        Returns:
            The verdict on each text the AI judged within the time limit. A text left
            out is decided by the word rule.
        """
        if self._judge is None or self._executor is None or not texts:
            return {}
        remembered: dict[str, HazardVerdict] = {
            text: verdict
            for text in texts
            if (verdict := self._remembered.get(text)) is not None
        }
        asked: dict[str, Future[HazardVerdict | None]] = {
            text: self._asking_about(text, self._judge, self._executor)
            for text in texts - remembered.keys()
        }
        if not asked:
            return remembered
        done, late = wait(asked.values(), timeout=self._time_limit_seconds)
        if late:
            _logger.warning(
                "The AI took longer than %s seconds to judge %d hazards, so the word "
                "rule decided.",
                self._time_limit_seconds,
                len(late),
            )
        answered: dict[str, HazardVerdict] = {
            text: verdict
            for text, future in asked.items()
            if future in done and (verdict := future.result()) is not None
        }
        return remembered | answered

    def _asking_about(
        self,
        hazard_text: str,
        judge: HazardJudge,
        executor: ThreadPoolExecutor,
    ) -> Future[HazardVerdict | None]:
        """Ask the AI about one text, unless it is being asked already or has answered.

        Args:
            hazard_text: What the AI is given about the hazard.
            judge: The AI to ask.
            executor: The threads that ask it.

        Returns:
            The answer to come: the one already on its way, one just remembered, or a
            new one.
        """
        with self._asking_lock:
            asking: Future[HazardVerdict | None] | None = self._asking.get(hazard_text)
            if asking is not None:
                return asking
            # An ask can finish between the caller's look in memory and here. It is
            # remembered before it leaves `_asking`, so one of the two looks finds it.
            remembered: HazardVerdict | None = self._remembered.get(hazard_text)
            if remembered is not None:
                answered: Future[HazardVerdict | None] = Future()
                answered.set_result(remembered)
                return answered
            asking = executor.submit(self._ask, hazard_text, judge)
            self._asking[hazard_text] = asking
            return asking

    def _ask(self, hazard_text: str, judge: HazardJudge) -> HazardVerdict | None:
        """Ask the AI about one hazard, and remember a usable verdict. Never raises.

        It runs in a background thread, so a verdict that comes after the time limit is
        still remembered, and used the next time the same words are checked.

        Args:
            hazard_text: What the AI is given about the hazard.
            judge: The AI to ask.

        Returns:
            The verdict, or None when the AI failed or its reply was unusable.
        """
        try:
            verdict: HazardVerdict | None = hazard_verdict(judge.judge(hazard_text))
        except Exception as error:  # Any AI failure at all means the word rule decides.
            _logger.warning(
                "The AI could not judge a hazard (%s), so the word rule decided.",
                ai_failure_kind(error),
                exc_info=not is_expected_ai_failure(error),
            )
            verdict = None
        else:
            if verdict is None:
                _logger.warning(
                    "The AI replied with none of its words, so the word rule decided.",
                )
            else:
                self._remembered.remember(hazard_text, verdict)
        finally:
            with self._asking_lock:
                self._asking.pop(hazard_text, None)
        return verdict
