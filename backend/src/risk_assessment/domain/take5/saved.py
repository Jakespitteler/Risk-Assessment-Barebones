"""An immutable submitted Take 5, including the verdict the worker was given."""

from datetime import datetime
from uuid import UUID

from risk_assessment.domain.take5.take5 import Take5
from risk_assessment.domain.take5.verdict import Verdict


class SavedTake5(Take5):
    """A Take 5 as it was saved: what the worker gave, and the verdict they were shown.

    It is never changed once saved, so it always shows the template and verdict the
    worker was given, even after the rules change.

    Attributes:
        id: The ID the phone made when the worker started submitting.
        created_at: When it was saved.
        worker_name: Who did the Take 5.
        job: What the job is.
        location: Where the job is.
        finished_at: When it was finished. Until task 0008 this is when it was saved.
        verdict: The verdict the worker was shown.
    """

    id: UUID
    created_at: datetime
    worker_name: str
    job: str
    location: str
    finished_at: datetime
    verdict: Verdict
