"""Asking the challenge question, answering it and finishing a Take 5 (spec C1 to C6).

Each test uses a stand-in for the AI that sends back whatever the spec's row says, or
fails, or takes too long. A real SQLite file in a temporary folder keeps what is saved.
"""

import logging
import threading
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from risk_assessment.domain.questions import Answer
from risk_assessment.domain.take5.challenge import AiQuestion, AskedBy, Challenge
from risk_assessment.domain.take5.draft import Take5Draft
from risk_assessment.domain.take5.saved import SavedTake5
from risk_assessment.domain.take5.template import BOOKLET_TEMPLATE
from risk_assessment.domain.take5.verdict import Verdict
from risk_assessment.services.ports import AiReplyError, ChallengeAsker
from risk_assessment.services.take5s import (
    AlreadyAnsweredError,
    InvalidAnswerError,
    Take5NotFoundError,
    Take5Service,
)
from risk_assessment.storage.sqlite import SqliteTake5Repository
from tests.samples import (
    SAMPLE_ANSWER,
    sample_answers,
    sample_draft,
    sample_hazard_draft,
)

EXAMPLE_40_QUESTION: str = "What stops the tray moving while you're on it?"
FALLBACK_ABOUT_THE_TRAY: str = (
    "What is the one thing that has to go right so that 'Fall from the tray' doesn't "
    "hurt anyone, and how will you check it before you start?"
)
# Long enough for the test to see the service give up, short enough to keep it fast.
SHORT_TIME_LIMIT_SECONDS: float = 0.05


class StandInAsker:
    """A stand-in for the AI: sends back a set reply, fails, or is slow.

    Attributes:
        texts_given: Every text the service sent, in order.
    """

    def __init__(
        self,
        reply: str = EXAMPLE_40_QUESTION,
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

    def ask(self, take5_text: str) -> AiQuestion:
        """Record the text, then reply, fail or wait as set.

        Args:
            take5_text: The Take 5, as the service wrote it out.

        Returns:
            The set reply, from a made-up model.

        Raises:
            Exception: The set failure, if there is one.
        """
        self.texts_given.append(take5_text)
        if self._wait_until is not None:
            self._wait_until.wait()
        if self._failure is not None:
            raise self._failure
        return AiQuestion(
            text=self._reply,
            model="example-model",
            instructions_version="1",
        )


def _service(
    tmp_path: Path,
    asker: ChallengeAsker | None = None,
) -> Take5Service:
    """Make a booklet service with an empty SQLite file and this AI.

    Args:
        tmp_path: pytest's temporary folder for this test.
        asker: The stand-in AI, or None for no AI set up.

    Returns:
        The service.
    """
    return Take5Service(
        SqliteTake5Repository(tmp_path / "take5.sqlite3"),
        BOOKLET_TEMPLATE,
        challenge_asker=asker,
        ai_time_limit_seconds=SHORT_TIME_LIMIT_SECONDS,
    )


def _tray_draft(**answers: Answer) -> Take5Draft:
    """Make example 18 with its hazard described as "Fall from the tray".

    Args:
        **answers: Answers to change, by question ID.

    Returns:
        The draft.
    """
    hazard = sample_hazard_draft().model_copy(
        update={"description": "Fall from the tray"},
    )
    return sample_draft(hazard).model_copy(
        update={"answers": sample_answers(**answers)},
    )


def test_example_40_the_ais_question_is_asked_and_saved_as_the_ais(
    tmp_path: Path,
) -> None:
    """The Take 5 is saved unfinished, with the AI's question and who asked (C1, C5)."""
    service: Take5Service = _service(tmp_path, StandInAsker())

    saved: SavedTake5 = service.submit(_tray_draft(), uuid4())

    assert saved.challenge == Challenge(
        question=EXAMPLE_40_QUESTION,
        asked_by=AskedBy.AI,
        model="example-model",
        instructions_version="1",
    )
    assert saved.verdict is None
    assert saved.finished_at is None
    assert service.get(saved.id) == saved


@pytest.mark.parametrize(
    "asker",
    [StandInAsker(failure=AiReplyError("The AI is down.")), None],
    ids=["fails", "not_set_up"],
)
def test_example_41_the_fallback_is_asked_when_the_ai_fails_or_is_not_set_up(
    tmp_path: Path,
    asker: StandInAsker | None,
) -> None:
    """The worker gets the fixed question, never an error (C3)."""
    saved: SavedTake5 = _service(tmp_path, asker).submit(_tray_draft(), uuid4())

    assert saved.challenge == Challenge(
        question=FALLBACK_ABOUT_THE_TRAY,
        asked_by=AskedBy.FALLBACK,
    )


def test_example_41_the_fallback_is_asked_when_the_ai_takes_too_long(
    tmp_path: Path,
) -> None:
    """The service stops waiting at the time limit (10 seconds when running)."""
    reply_allowed = threading.Event()
    service: Take5Service = _service(tmp_path, StandInAsker(wait_until=reply_allowed))
    try:
        saved: SavedTake5 = service.submit(_tray_draft(), uuid4())
    finally:
        reply_allowed.set()

    assert saved.challenge is not None
    assert saved.challenge.question == FALLBACK_ABOUT_THE_TRAY


def test_example_45_the_trimmed_question_is_saved(tmp_path: Path) -> None:
    """The question shown is the AI's, without the spaces around it (C2)."""
    asker = StandInAsker(reply=f"  {EXAMPLE_40_QUESTION}\n")

    saved: SavedTake5 = _service(tmp_path, asker).submit(_tray_draft(), uuid4())

    assert saved.challenge is not None
    assert saved.challenge.question == EXAMPLE_40_QUESTION


def test_example_46_a_reply_that_is_not_a_question_gets_the_fallback(
    tmp_path: Path,
) -> None:
    """An apology is thrown away, and the fixed question asked instead (C2, C3)."""
    asker = StandInAsker(reply="I can't help with that request.")

    saved: SavedTake5 = _service(tmp_path, asker).submit(_tray_draft(), uuid4())

    assert saved.challenge is not None
    assert saved.challenge.asked_by is AskedBy.FALLBACK


def test_example_49_the_workers_name_is_not_given_to_the_ai(tmp_path: Path) -> None:
    """Sam Example submits; the text the AI gets never contains the name (C1)."""
    asker = StandInAsker()

    _service(tmp_path, asker).submit(_tray_draft(), uuid4())

    assert len(asker.texts_given) == 1
    assert "Sam Example" not in asker.texts_given[0]
    assert "Change tyre on LV12" in asker.texts_given[0]


def test_example_52_a_four_word_answer_finishes_the_take5(tmp_path: Path) -> None:
    """The answer is saved, and the verdict is example 18's (C4, C5)."""
    service: Take5Service = _service(tmp_path, StandInAsker())
    saved: SavedTake5 = service.submit(_tray_draft(), uuid4())

    finished: SavedTake5 = service.answer(saved.id, f"  {SAMPLE_ANSWER} ")

    assert finished.verdict == Verdict(can_start=True, reasons=())
    assert finished.finished_at is not None
    assert finished.challenge is not None
    assert finished.challenge.answer == SAMPLE_ANSWER
    assert finished.challenge.question == EXAMPLE_40_QUESTION
    assert service.get(saved.id) == finished


@pytest.mark.parametrize(
    "short_answer",
    [
        pytest.param("Yes", id="test_example_50_one_word"),
        pytest.param("Chocked both sides", id="test_example_51_three_words"),
    ],
)
def test_examples_50_and_51_a_short_answer_is_refused_and_nothing_changes(
    tmp_path: Path,
    short_answer: str,
) -> None:
    """A one-word or three-word answer leaves the Take 5 unfinished (C4)."""
    service: Take5Service = _service(tmp_path)
    saved: SavedTake5 = service.submit(_tray_draft(), uuid4())

    with pytest.raises(InvalidAnswerError) as refusal:
        service.answer(saved.id, short_answer)

    assert refusal.value.error.path == "answer"
    assert service.get(saved.id) == saved


def test_example_53_a_good_answer_does_not_change_the_verdict(tmp_path: Path) -> None:
    """Example 19 (permits is No), answered as in example 52, still stops (C5)."""
    service: Take5Service = _service(tmp_path)
    saved: SavedTake5 = service.submit(_tray_draft(permits=Answer.NO), uuid4())

    finished: SavedTake5 = service.answer(saved.id, SAMPLE_ANSWER)

    assert finished.verdict is not None
    assert not finished.verdict.can_start


def test_example_54_an_unanswered_take5_stays_unfinished_with_its_question(
    tmp_path: Path,
) -> None:
    """Opening it again shows the same question, and it has no verdict (C6)."""
    asker = StandInAsker()
    service: Take5Service = _service(tmp_path, asker)
    submission_id: UUID = uuid4()
    saved: SavedTake5 = service.submit(_tray_draft(), submission_id)

    reopened: SavedTake5 | None = service.get(submission_id)
    retried: SavedTake5 = service.submit(_tray_draft(), submission_id)

    assert reopened == saved
    assert retried == saved
    assert saved.verdict is None
    assert len(asker.texts_given) == 1


def test_example_55_a_second_answer_is_refused_and_the_first_is_kept(
    tmp_path: Path,
) -> None:
    """A finished Take 5 is never changed (C6)."""
    service: Take5Service = _service(tmp_path)
    saved: SavedTake5 = service.submit(_tray_draft(), uuid4())
    finished: SavedTake5 = service.answer(saved.id, SAMPLE_ANSWER)

    with pytest.raises(AlreadyAnsweredError):
        service.answer(saved.id, "Someone else checked the chocks")

    assert service.get(saved.id) == finished


def test_the_same_answer_sent_again_gets_the_finished_take5(tmp_path: Path) -> None:
    """A retry after a lost reply is the same answer, not a second one."""
    service: Take5Service = _service(tmp_path)
    saved: SavedTake5 = service.submit(_tray_draft(), uuid4())
    finished: SavedTake5 = service.answer(saved.id, SAMPLE_ANSWER)

    assert service.answer(saved.id, SAMPLE_ANSWER) == finished


def test_example_56_a_saved_take5_with_no_question_is_given_the_fallback(
    tmp_path: Path,
) -> None:
    """The app stopped between saving and asking: opening it asks the fixed one (C6)."""
    asker = StandInAsker()
    service: Take5Service = _service(tmp_path, asker)
    repository = SqliteTake5Repository(tmp_path / "take5.sqlite3")
    saved: SavedTake5 = service.submit(_tray_draft(), uuid4())
    repository.add(
        saved.model_copy(update={"id": uuid4(), "challenge": None}),
    )
    without_question: SavedTake5 = repository.list_newest_first()[0]

    opened: SavedTake5 | None = service.get(without_question.id)

    assert opened is not None
    assert opened.challenge == Challenge(
        question=FALLBACK_ABOUT_THE_TRAY,
        asked_by=AskedBy.FALLBACK,
    )
    assert service.get(without_question.id) == opened
    assert len(asker.texts_given) == 1


def test_a_take5_finished_before_the_question_existed_cannot_be_answered(
    tmp_path: Path,
) -> None:
    """One finished before task 0008 has a verdict and no question; it stays so."""
    service: Take5Service = _service(tmp_path)
    saved: SavedTake5 = service.submit(_tray_draft(), uuid4())
    finished: SavedTake5 = service.answer(saved.id, SAMPLE_ANSWER)
    repository = SqliteTake5Repository(tmp_path / "take5.sqlite3")
    old_style: SavedTake5 = repository.add(
        finished.model_copy(update={"id": uuid4(), "challenge": None}),
    )

    with pytest.raises(AlreadyAnsweredError):
        service.answer(old_style.id, SAMPLE_ANSWER)

    assert service.get(old_style.id) == old_style


def test_answering_a_take5_that_is_not_saved_is_refused(tmp_path: Path) -> None:
    """There is nothing to answer."""
    with pytest.raises(Take5NotFoundError):
        _service(tmp_path).answer(uuid4(), SAMPLE_ANSWER)


def test_a_failed_ai_question_logs_one_line_naming_the_kind_without_a_trace(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A handled AI failure is one warning, with no stack trace (task 0028)."""
    asker = StandInAsker(failure=AiReplyError("Sam Example's job text"))

    with caplog.at_level(logging.WARNING, logger="risk_assessment"):
        _service(tmp_path, asker).submit(_tray_draft(), uuid4())

    (warning,) = [record for record in caplog.records if record.levelname == "WARNING"]
    assert warning.getMessage() == (
        "The AI could not ask a question (AiReplyError), so the fixed one was asked."
    )
    assert not warning.exc_info
    assert "Sam Example" not in caplog.text


def test_a_bug_while_asking_the_ai_still_falls_back_but_keeps_its_trace(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A TypeError is a bug in the app, not an AI failure (task 0028).

    The worker still gets the fixed question, and the log keeps the trace so it can be
    fixed.
    """
    asker = StandInAsker(failure=TypeError("a bug"))

    with caplog.at_level(logging.WARNING, logger="risk_assessment"):
        saved: SavedTake5 = _service(tmp_path, asker).submit(_tray_draft(), uuid4())

    (warning,) = [record for record in caplog.records if record.levelname == "WARNING"]
    assert "(TypeError)" in warning.getMessage()
    assert warning.exc_info is not None
    assert saved.challenge is not None
    assert saved.challenge.asked_by == AskedBy.FALLBACK
