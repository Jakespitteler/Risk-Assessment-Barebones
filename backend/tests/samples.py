"""Made-up Take 5s that tests in more than one folder share.

Every builder makes the same example unless a test asks for something different:
Sam Example changing a tyre on LV12, with one hazard, a moving wheel, rated
8 Moderate before a barricade and 5 Low after it. A test passes arguments, or calls
`model_copy`, to change only the part it is about.

These are plain functions rather than pytest fixtures, so a test can pass them
arguments and pyright checks each call. pytest's own advice is not to import from a
`conftest.py`, so they live here instead.
"""

from datetime import UTC, datetime
from uuid import uuid4

from risk_assessment.domain.controls import Control, ControlKind
from risk_assessment.domain.risk import rate
from risk_assessment.domain.take5.draft import (
    ControlDraft,
    HazardDraft,
    RatingChoice,
    Take5Draft,
)
from risk_assessment.domain.take5.saved import SavedTake5
from risk_assessment.domain.take5.take5 import Hazard
from risk_assessment.domain.take5.template import BOOKLET_MATRIX, BOOKLET_TEMPLATE
from risk_assessment.domain.take5.verdict import Verdict

BARRICADE = Control(description="Barricade the area", kind=ControlKind.BARRICADE)
BARRICADE_DRAFT = ControlDraft(
    description="Barricade the area",
    kind=ControlKind.BARRICADE,
)
GOOD_TO_GO = Verdict(can_start=True, reasons=())


def sample_hazard_draft(
    before: tuple[str, str] = ("Possible", "Minor"),
    after: tuple[str, str] = ("Unlikely", "Minor"),
    controls: tuple[ControlDraft, ...] = (BARRICADE_DRAFT,),
) -> HazardDraft:
    """Make a complete hazard as the phone sends it: 8 then 5 with a barricade.

    Args:
        before: The likelihood and consequence before controls.
        after: The likelihood and consequence after controls.
        controls: The controls.

    Returns:
        The hazard, not yet rated.
    """
    return HazardDraft(
        description="Moving wheel",
        before=RatingChoice(likelihood=before[0], consequence=before[1]),
        controls=controls,
        after=RatingChoice(likelihood=after[0], consequence=after[1]),
    )


def sample_draft(*hazards: HazardDraft) -> Take5Draft:
    """Make a complete Take 5 as the phone sends it.

    Args:
        *hazards: Its hazards. With none, it has the one from `sample_hazard_draft()`.

    Returns:
        The draft, ready to check or submit.
    """
    return Take5Draft(
        worker_name="Sam Example",
        job="Change tyre on LV12",
        location="Example workshop",
        hazards=hazards or (sample_hazard_draft(),),
    )


def sample_uncontrolled_draft() -> Take5Draft:
    """Make the spec's example 22: the sample draft's hazard without controls.

    Returns:
        The draft, with no controls and no after rating. It can be submitted, but
        its verdict is Don't start yet.
    """
    hazard: HazardDraft = sample_hazard_draft().model_copy(
        update={"controls": (), "after": RatingChoice()},
    )
    return sample_draft(hazard)


def sample_hazard(
    before: tuple[str, str] = ("Possible", "Minor"),
    after: tuple[str, str] = ("Unlikely", "Minor"),
    controls: tuple[Control, ...] = (BARRICADE,),
) -> Hazard:
    """Make a hazard rated on the booklet's matrix: 8 then 5 with a barricade.

    Args:
        before: The likelihood and consequence before controls.
        after: The likelihood and consequence after controls.
        controls: The controls.

    Returns:
        The rated hazard.
    """
    return Hazard(
        description="Moving wheel",
        before=rate(BOOKLET_MATRIX, *before),
        controls=controls,
        after=rate(BOOKLET_MATRIX, *after),
    )


def sample_saved_take5(
    verdict: Verdict = GOOD_TO_GO,
    job: str = "Change tyre on LV12",
) -> SavedTake5:
    """Make a saved Take 5 with every field filled in and one `sample_hazard()`.

    Args:
        verdict: The verdict it was saved with.
        job: The job.

    Returns:
        The saved Take 5, with a new ID each time.
    """
    saved_at: datetime = datetime(2026, 11, 13, 7, 30, tzinfo=UTC)
    return SavedTake5(
        template=BOOKLET_TEMPLATE,
        hazards=(sample_hazard(),),
        id=uuid4(),
        created_at=saved_at,
        finished_at=saved_at,
        worker_name="Sam Example",
        job=job,
        location="Example workshop",
        verdict=verdict,
    )
