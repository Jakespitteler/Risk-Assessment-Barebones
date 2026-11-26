"""Tests for the patterns-over-time service (spec S1)."""

from datetime import timedelta
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest

from risk_assessment.domain.take5.patterns import Patterns
from risk_assessment.domain.take5.template import BOOKLET_TEMPLATE
from risk_assessment.services.patterns import PatternsService
from risk_assessment.storage.sqlite import SqliteTake5Repository
from tests.domain.take5.test_table import SATURDAY_MORNING, started


@pytest.fixture
def repository(tmp_path: Path) -> SqliteTake5Repository:
    """Give the test its own empty SQLite database.

    Args:
        tmp_path: pytest's temporary folder for this test.

    Returns:
        The repository.
    """
    return SqliteTake5Repository(tmp_path / "take5.sqlite3")


def test_every_saved_take5_counts_however_old(
    repository: SqliteTake5Repository,
) -> None:
    """S1: a Take 5 from a year ago counts beside today's, read in the asker's zone."""
    repository.add(started(SATURDAY_MORNING))
    repository.add(
        started(SATURDAY_MORNING - timedelta(days=365)).model_copy(
            update={"id": uuid4()},
        ),
    )

    patterns: Patterns = PatternsService(repository, BOOKLET_TEMPLATE).patterns(
        ZoneInfo("Australia/Perth"),
    )

    assert patterns.take5_count == 2
    assert [counts.group for counts in patterns.by_month] == [
        "November 2025",
        "November 2026",
    ]
