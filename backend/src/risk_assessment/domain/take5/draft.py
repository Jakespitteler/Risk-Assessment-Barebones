"""Check a Take 5 the worker is still filling in, and rate it once it is complete.

The phone sends only the worker's choices, never a score or a band. Every gap is
reported in one pass, each with the dotted path of the field it belongs beside, such as
`hazards.0.before.likelihood`. Warnings are reported the same way: they don't stop
the draft being submitted, but they say what will stop the job.
"""

from typing import ClassVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from risk_assessment.domain.controls import Control, ControlKind
from risk_assessment.domain.risk import RiskMatrix, RiskRating, rate
from risk_assessment.domain.take5.take5 import Hazard, Take5
from risk_assessment.domain.take5.template import Take5Template

FILL_IN_MESSAGE: str = "Fill in this field."
NO_HAZARD_MESSAGE: str = "List at least one hazard."
NO_KIND_MESSAGE: str = "Pick a control kind."
HIGHER_AFTER_MESSAGE: str = "Controls cannot make the after risk higher than before."
NO_CONTROLS_WARNING: str = "No controls: you'll be told not to start."


class RatingChoice(BaseModel):
    """A likelihood and a consequence as the worker picked them; neither is preset.

    Attributes:
        likelihood: The picked likelihood, or None until one is picked.
        consequence: The picked consequence, or None until one is picked.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    likelihood: str | None = None
    consequence: str | None = None


class ControlDraft(BaseModel):
    """A control whose wording or kind may still be missing.

    Attributes:
        description: What the worker will do, in their own words.
        kind: The kind of control, or None until one is picked.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    description: str = ""
    kind: ControlKind | None = None


class HazardDraft(BaseModel):
    """A hazard while the worker is still rating it and writing its controls.

    Attributes:
        description: The hazard in the worker's own words.
        before: The rating before controls.
        controls: The controls, possibly none.
        after: The rating after controls. Ignored when there are no controls (R6).
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    description: str = ""
    before: RatingChoice = Field(default_factory=RatingChoice)
    controls: tuple[ControlDraft, ...] = ()
    after: RatingChoice = Field(default_factory=RatingChoice)


class Take5Draft(BaseModel):
    """A Take 5 that hasn't been saved, as the phone sends it.

    Attributes:
        worker_name: Who is doing the Take 5.
        job: What the job is.
        location: Where the job is.
        hazards: The hazards, in the order the worker listed them.
        fixes: The ID of the saved Take 5 this one fixes, or None for a fresh one.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    worker_name: str = ""
    job: str = ""
    location: str = ""
    hazards: tuple[HazardDraft, ...] = ()
    fixes: UUID | None = None


class FieldError(BaseModel):
    """One gap or mistake, and the field it belongs beside.

    Attributes:
        path: The field's dotted path, such as `hazards.0.controls.1.kind`.
        message: What to do about it, in plain words.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    path: str
    message: str


class FieldWarning(BaseModel):
    """Something allowed that will stop the job, and the field it belongs beside.

    Attributes:
        path: The field's dotted path, such as `hazards.0.controls`.
        message: What it will mean, in plain words.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    path: str
    message: str


class DraftCheck(BaseModel):
    """What checking a draft found.

    Attributes:
        errors: Every gap or mistake, in the order of the form.
        warnings: Everything allowed that will stop the job, in the order of the form.
            A warning never stops the draft being submitted.
        assessment: The rated Take 5, or None while there are errors.
        can_submit: True when there are no errors.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    errors: tuple[FieldError, ...]
    warnings: tuple[FieldWarning, ...]
    assessment: Take5 | None
    can_submit: bool


def check_draft(draft: Take5Draft, template: Take5Template) -> DraftCheck:
    """Check every field of a draft in one pass, and rate it if nothing is missing.

    Args:
        draft: The worker's answers so far.
        template: The template the draft is filled in on.

    Returns:
        The errors and warnings, and the rated Take 5 when there are no errors.
    """
    errors: list[FieldError] = []
    for path, value in (
        ("worker_name", draft.worker_name),
        ("job", draft.job),
        ("location", draft.location),
    ):
        _required_text(value, path, errors)
    if not draft.hazards:
        errors.append(FieldError(path="hazards", message=NO_HAZARD_MESSAGE))
    hazards: list[Hazard] = []
    for index, hazard_draft in enumerate(draft.hazards):
        hazard: Hazard | None = _hazard(
            hazard_draft,
            template.matrix,
            f"hazards.{index}",
            errors,
        )
        if hazard is not None:
            hazards.append(hazard)
    assessment: Take5 | None = (
        None if errors else Take5(template=template, hazards=tuple(hazards))
    )
    return DraftCheck(
        errors=tuple(errors),
        warnings=_warnings(draft),
        assessment=assessment,
        can_submit=not errors,
    )


def _warnings(draft: Take5Draft) -> tuple[FieldWarning, ...]:
    """Warn about each hazard with no controls, which will mean Don't start yet (V2).

    Args:
        draft: The worker's answers so far.

    Returns:
        One warning for each hazard with no controls, on its `controls` path.
    """
    return tuple(
        FieldWarning(path=f"hazards.{index}.controls", message=NO_CONTROLS_WARNING)
        for index, hazard in enumerate(draft.hazards)
        if not hazard.controls
    )


def _hazard(
    draft: HazardDraft,
    matrix: RiskMatrix,
    path: str,
    errors: list[FieldError],
) -> Hazard | None:
    """Check one hazard and rate it.

    With no controls the after rating is the before rating (R6), and controls can't
    make the after score higher than the before score (R6).

    Args:
        draft: The hazard as the worker filled it in.
        matrix: The matrix to rate it on.
        path: The hazard's dotted path, such as `hazards.0`.
        errors: Where to add any errors found.

    Returns:
        The rated hazard, or None if it has any error.
    """
    errors_before: int = len(errors)
    description: str = _required_text(draft.description, f"{path}.description", errors)
    before: RiskRating | None = _rating(draft.before, matrix, f"{path}.before", errors)
    controls: list[Control] = []
    for index, control_draft in enumerate(draft.controls):
        control: Control | None = _control(
            control_draft,
            f"{path}.controls.{index}",
            errors,
        )
        if control is not None:
            controls.append(control)
    after: RiskRating | None = (
        _rating(draft.after, matrix, f"{path}.after", errors)
        if draft.controls
        else before
    )
    if before is not None and after is not None and after.score > before.score:
        errors.append(FieldError(path=f"{path}.after", message=HIGHER_AFTER_MESSAGE))
    if len(errors) > errors_before or before is None or after is None:
        return None
    return Hazard(
        description=description,
        before=before,
        controls=tuple(controls),
        after=after,
    )


def _control(
    draft: ControlDraft,
    path: str,
    errors: list[FieldError],
) -> Control | None:
    """Check one control.

    Args:
        draft: The control as the worker filled it in.
        path: The control's dotted path, such as `hazards.0.controls.1`.
        errors: Where to add any errors found.

    Returns:
        The control, or None if its wording or its kind is missing.
    """
    description: str = _required_text(draft.description, f"{path}.description", errors)
    if draft.kind is None:
        errors.append(FieldError(path=f"{path}.kind", message=NO_KIND_MESSAGE))
        return None
    if not description:
        return None
    return Control(description=description, kind=draft.kind)


def _rating(
    choice: RatingChoice,
    matrix: RiskMatrix,
    path: str,
    errors: list[FieldError],
) -> RiskRating | None:
    """Check that both halves of a rating are picked, then look it up (R1).

    Args:
        choice: What the worker picked.
        matrix: The matrix to look the rating up on.
        path: The rating's dotted path, such as `hazards.0.before`.
        errors: Where to add any errors found.

    Returns:
        The rating, or None if either half is missing or not on the matrix's scale.
    """
    likelihood: str | None = _picked(
        choice.likelihood,
        matrix.likelihoods,
        f"{path}.likelihood",
        errors,
    )
    consequence: str | None = _picked(
        choice.consequence,
        matrix.consequences,
        f"{path}.consequence",
        errors,
    )
    if likelihood is None or consequence is None:
        return None
    return rate(matrix, likelihood, consequence)


def _picked(
    level: str | None,
    scale: tuple[str, ...],
    path: str,
    errors: list[FieldError],
) -> str | None:
    """Check that a level was picked from a scale.

    Args:
        level: The level the worker picked, or None.
        scale: The levels that can be picked.
        path: The field's dotted path, ending in `likelihood` or `consequence`.
        errors: Where to add an error if the level is missing.

    Returns:
        The level, or None if it is missing or not on the scale.
    """
    if level is None or level not in scale:
        scale_name: str = path.rsplit(".", 1)[-1]
        errors.append(FieldError(path=path, message=f"Pick a {scale_name}."))
        return None
    return level


def _required_text(value: str, path: str, errors: list[FieldError]) -> str:
    """Trim an answer, and report it if it is blank.

    Args:
        value: What the worker typed.
        path: The field's dotted path.
        errors: Where to add an error if the answer is blank.

    Returns:
        The answer without spaces at either end.
    """
    cleaned: str = value.strip()
    if not cleaned:
        errors.append(FieldError(path=path, message=FILL_IN_MESSAGE))
    return cleaned
