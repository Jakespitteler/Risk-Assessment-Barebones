"""An immutable submitted Take 5, including the verdict the worker was given."""

from datetime import datetime
from uuid import UUID

from risk_assessment.domain.take5.take5 import Take5
from risk_assessment.domain.take5.verdict import Verdict


class SavedTake5(Take5):
    """Add submission details to the scoring model without changing its rules."""

    id: UUID
    created_at: datetime
    worker_name: str
    job: str
    location: str
    finished_at: datetime
    verdict: Verdict
