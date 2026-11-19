"""Judging vague hazards with an AI, and the word rule when it can't (spec T6).

Each test uses a stand-in for the AI that sends back whatever the spec's row says, or
fails, or takes too long.
"""

import threading
import time

import pytest

from risk_assessment.domain.questions import Answer
from risk_assessment.domain.take5.draft import HazardDraft, Take5Draft
from risk_assessment.domain.take5.hazard_nudges import (
    HAZARD_AI_TIME_LIMIT_SECONDS,
    HazardVerdict,
    Nudge,
)
from risk_assessment.domain.take5.template import BOOKLET_TEMPLATE, Take5Template
from risk_assessment.services.hazard_nudges import HazardNudger, RememberedVerdicts
from tests.samples import sample_answers, sample_draft, sample_hazard_draft

# Long enough for the test to see the nudger give up, short enough to keep it fast.
SHORT_TIME_LIMIT_SECONDS: float = 0.05
# Long enough for a stand-in that answers at once, so a slow machine can't fail a test.
PLENTY_OF_TIME_SECONDS: float = 5


class StandInJudge:
    """A stand-in for the AI: sends back a set reply, fails, or is slow.

    Attributes:
        texts_given: Every text it was sent, in order.
        answered: Set once it has replied, so a test can wait for a late answer.
    """

    def __init__(
        self,
        reply: str = "specific",
        failure: Exception | None = None,
        wait_until: threading.Event | None = None,
    ) -> None:
        """Set what the stand-in does when it is asked.

        Args:
            reply: The text it sends back.
            failure: An error to raise instead of replying, or None.
            wait_until: An event to wait for before replying, to act slow, or None.
        """
        self._reply: str = reply
        self._failure: Exception | None = failure
        self._wait_until: threading.Event | None = wait_until
        self.texts_given: list[str] = []
        self.answered: threading.Event = threading.Event()

    def judge(self, hazard_text: str) -> str:
        """Record the text, then reply, fail or wait as set.

        Args:
            hazard_text: The hazard, as the nudger wrote it out.

        Returns:
            The set reply.

        Raises:
            Exception: The set failure, if there is one.
        """
        self.texts_given.append(hazard_text)
        if self._wait_until is not None:
            self._wait_until.wait(timeout=PLENTY_OF_TIME_SECONDS)
        try:
            if self._failure is not None:
                raise self._failure
            return self._reply
        finally:
            self.answered.set()


def _linked_to_vehicles(
    description: str,
    job: str = "Change the front left tyre on LV12",
) -> Take5Draft:
    """Make the spec's T6 draft: one hazard, linked to the vehicles question's Yes.

    Args:
        description: The hazard in the worker's words.
        job: What the job is.

    Returns:
        The draft, by "Sam Example", in the light vehicle workshop.
    """
    hazard: HazardDraft = sample_hazard_draft().model_copy(
        update={"description": description, "covers": ("vehicles",)},
    )
    return sample_draft(hazard).model_copy(
        update={
            "answers": sample_answers(vehicles=Answer.YES),
            "job": job,
            "location": "Light vehicle workshop",
        },
    )


def _nudger(
    judge: StandInJudge | None,
    time_limit_seconds: float = PLENTY_OF_TIME_SECONDS,
    template: Take5Template = BOOKLET_TEMPLATE,
) -> HazardNudger:
    """Make a nudger on the booklet with a stand-in AI.

    Args:
        judge: The stand-in, or None for no AI.
        time_limit_seconds: How long it waits for the stand-in.
        template: The template drafts are filled in on.

    Returns:
        The nudger.
    """
    return HazardNudger(template, judge, time_limit_seconds)


def test_example_77_the_ais_specific_beats_the_word_count() -> None:
    """T6: "Crusher dust" is two words, but the AI says it is specific."""
    judge = StandInJudge("specific")

    assert _nudger(judge).nudges(_linked_to_vehicles("Crusher dust")) == ()
    assert len(judge.texts_given) == 1


def test_example_78_the_ais_vague_beats_the_word_count() -> None:
    """T6: seven words, but the AI says vague, so it is nudged."""
    judge = StandInJudge("vague")
    draft: Take5Draft = _linked_to_vehicles("There are some hazards around here today")

    nudges: tuple[Nudge, ...] = _nudger(judge).nudges(draft)

    assert [nudge.question_id for nudge in nudges] == ["vehicles"]


def test_example_79_a_dressed_up_reply_still_counts() -> None:
    """T6: "  Vague." with a line break is read as vague."""
    judge = StandInJudge("  Vague.\n")
    draft: Take5Draft = _linked_to_vehicles("There are some hazards around here today")

    assert len(_nudger(judge).nudges(draft)) == 1


@pytest.mark.parametrize(
    "judge",
    [
        StandInJudge(failure=RuntimeError("The AI is down.")),
        None,
    ],
    ids=["the AI fails", "no AI is set up"],
)
def test_example_80_without_the_ai_the_word_rule_decides(
    judge: StandInJudge | None,
) -> None:
    """T6: "Get hit by a car" is five words, one short, so it is nudged."""
    assert len(_nudger(judge).nudges(_linked_to_vehicles("Get hit by a car"))) == 1
    assert (
        len(
            _nudger(judge).nudges(
                _linked_to_vehicles("Hit by a truck reversing nearby"),
            ),
        )
        == 0
    )


def test_example_80_too_slow_an_ai_leaves_the_word_rule_to_decide() -> None:
    """T6: an AI that takes longer than the time limit isn't waited for."""
    never_answer = threading.Event()
    judge = StandInJudge("specific", wait_until=never_answer)

    nudges: tuple[Nudge, ...] = _nudger(judge, SHORT_TIME_LIMIT_SECONDS).nudges(
        _linked_to_vehicles("Get hit by a car"),
    )

    never_answer.set()
    assert len(nudges) == 1


def test_example_81_an_unusable_reply_leaves_the_word_rule_to_decide() -> None:
    """T6: "It depends on the site." isn't a verdict, so two words are nudged."""
    judge = StandInJudge("It depends on the site.")

    assert len(_nudger(judge).nudges(_linked_to_vehicles("Crusher dust"))) == 1


def test_example_82_the_same_words_are_judged_once() -> None:
    """T6: checking example 77 again uses the remembered answer."""
    judge = StandInJudge("specific")
    nudger: HazardNudger = _nudger(judge)

    nudger.nudges(_linked_to_vehicles("Crusher dust"))
    second: tuple[Nudge, ...] = nudger.nudges(_linked_to_vehicles("Crusher dust"))

    assert second == ()
    assert len(judge.texts_given) == 1


def test_example_83_a_different_job_is_judged_again() -> None:
    """T6: an answer is remembered only for the same hazard, question, job, place."""
    judge = StandInJudge("specific")
    nudger: HazardNudger = _nudger(judge)

    nudger.nudges(_linked_to_vehicles("Crusher dust"))
    nudger.nudges(
        _linked_to_vehicles("Crusher dust", job="Clean up under the primary crusher"),
    )

    assert len(judge.texts_given) == 2


def test_an_unusable_reply_is_not_remembered() -> None:
    """The AI is asked again next time, as a later reply may be usable."""
    judge = StandInJudge("It depends on the site.")
    nudger: HazardNudger = _nudger(judge)

    nudger.nudges(_linked_to_vehicles("Crusher dust"))
    nudger.nudges(_linked_to_vehicles("Crusher dust"))

    assert len(judge.texts_given) == 2


def test_example_84_a_late_answer_is_used_next_time() -> None:
    """T6: too late for the first check, the AI's "specific" decides the second."""
    let_it_answer = threading.Event()
    judge = StandInJudge("specific", wait_until=let_it_answer)
    nudger: HazardNudger = _nudger(judge, SHORT_TIME_LIMIT_SECONDS)

    first: tuple[Nudge, ...] = nudger.nudges(_linked_to_vehicles("Get hit by a car"))
    let_it_answer.set()
    second: tuple[Nudge, ...] = _check_until_settled(
        nudger,
        _linked_to_vehicles("Get hit by a car"),
    )

    assert len(first) == 1
    assert second == ()
    assert len(judge.texts_given) == 1


def _check_until_settled(nudger: HazardNudger, draft: Take5Draft) -> tuple[Nudge, ...]:
    """Check a draft again and again until the late answer is used, or time is up.

    The late answer is stored a moment after the stand-in replies. A check before then
    waits for the same ask, never a new one, so checking again is safe when slow.

    Args:
        nudger: The nudger that asked.
        draft: The same draft as before.

    Returns:
        The first check's nudges once there are none, or the last check's at the end.
    """
    deadline: float = time.monotonic() + PLENTY_OF_TIME_SECONDS
    nudges: tuple[Nudge, ...] = nudger.nudges(draft)
    while nudges and time.monotonic() < deadline:
        nudges = nudger.nudges(draft)
    return nudges


def test_two_checks_at_once_share_one_ask() -> None:
    """A second check of words still with the AI waits for the same answer."""
    let_it_answer = threading.Event()
    judge = StandInJudge("specific", wait_until=let_it_answer)
    nudger: HazardNudger = _nudger(judge)
    results: list[tuple[Nudge, ...]] = []

    checks: list[threading.Thread] = [
        threading.Thread(
            target=lambda: results.append(
                nudger.nudges(_linked_to_vehicles("Crusher dust")),
            ),
        )
        for _ in range(2)
    ]
    for check in checks:
        check.start()
    # Answer only once the first ask is with the AI and the second check is waiting.
    deadline: float = time.monotonic() + PLENTY_OF_TIME_SECONDS
    while not judge.texts_given and time.monotonic() < deadline:
        time.sleep(0.01)
    time.sleep(0.1)
    let_it_answer.set()
    for check in checks:
        check.join(timeout=PLENTY_OF_TIME_SECONDS)

    assert results == [(), ()]
    assert len(judge.texts_given) == 1


def test_example_85_the_workers_name_is_never_sent() -> None:
    """T6: the stand-in is given the hazard, question, job and place, not the name."""
    judge = StandInJudge("specific")

    _nudger(judge).nudges(_linked_to_vehicles("Crusher dust"))

    assert "Sam Example" not in judge.texts_given[0]
    assert "Crusher dust" in judge.texts_given[0]
    assert "Light vehicle workshop" in judge.texts_given[0]


def test_example_87_the_ai_is_not_asked_when_there_is_nothing_to_judge() -> None:
    """T6: no Yes link, a blank hazard, or no minimum means no ask and no nudge."""
    judge = StandInJudge("vague")
    unlinked: Take5Draft = sample_draft(
        sample_hazard_draft().model_copy(update={"description": "Crusher dust"}),
    )
    no_minimum: Take5Template = BOOKLET_TEMPLATE.model_copy(
        update={"specific_hazard_words": None},
    )

    assert _nudger(judge).nudges(unlinked) == ()
    assert _nudger(judge).nudges(_linked_to_vehicles("   ")) == ()
    assert (
        _nudger(judge, template=no_minimum).nudges(
            _linked_to_vehicles("Crusher dust"),
        )
        == ()
    )
    assert judge.texts_given == []


def test_the_oldest_verdict_is_forgotten_past_the_limit() -> None:
    """Memory stays bounded however long the server runs."""
    remembered = RememberedVerdicts(limit=2)

    remembered.remember("first", HazardVerdict.VAGUE)
    remembered.remember("second", HazardVerdict.SPECIFIC)
    remembered.remember("third", HazardVerdict.VAGUE)

    assert remembered.get("first") is None
    assert remembered.get("second") is HazardVerdict.SPECIFIC
    assert remembered.get("third") is HazardVerdict.VAGUE


def test_the_ai_has_five_seconds() -> None:
    """Decision D57: the word rule decides after 5 seconds."""
    assert HAZARD_AI_TIME_LIMIT_SECONDS == 5
