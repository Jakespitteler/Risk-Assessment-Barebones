"""A submitted Take 5: unfinished until its question is answered, then never changed."""

from datetime import datetime
from uuid import UUID

from risk_assessment.domain.take5.challenge import Challenge
from risk_assessment.domain.take5.take5 import Take5
from risk_assessment.domain.take5.verdict import Verdict


class SavedTake5(Take5):
    """A Take 5 as it was saved: what the worker gave, and the verdict they were shown.

    It is saved unfinished, before the challenge question is asked (spec C6). The
    question is added once, then the answer and the verdict once, and from then on it
    is never changed, so it always shows the template and verdict the worker was
    given, even after the rules change.

    Attributes:
        id: The ID the phone made when the worker started submitting.
        created_at: When it was saved.
        worker_name: Who did the Take 5.
        job: What the job is.
        location: Where the job is.
        finished_at: When the challenge question was answered, or None while it is
            unfinished. A Take 5 saved before task 0008 was finished when it was saved.
        verdict: The verdict the worker was shown, or None while it is unfinished.
        fixes: The ID of the saved Take 5 this one fixes, or None. It points back
            only, so the first Take 5 is never changed when it is fixed.
        started_at: When the worker started it, by the phone's clock, or None for a
            Take 5 saved before task 0019.
        challenge: The question it was asked and the worker's answer, or None until
            it is asked. A Take 5 finished before task 0008 has none.
    """

    id: UUID
    created_at: datetime
    worker_name: str
    job: str
    location: str
    finished_at: datetime | None = None
    verdict: Verdict | None = None
    fixes: UUID | None = None
    started_at: datetime | None = None
    challenge: Challenge | None = None

    @property
    def is_finished(self) -> bool:
        """Whether the challenge question has been answered and the verdict given."""
        return self.verdict is not None
