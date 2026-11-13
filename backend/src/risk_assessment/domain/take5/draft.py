"""Check incomplete worker input and turn valid choices into matrix ratings."""

from pydantic import BaseModel, Field, ValidationError

from risk_assessment.domain.controls import Control, ControlKind
from risk_assessment.domain.risk import RiskRating, rate
from risk_assessment.domain.take5.take5 import Hazard, Take5
from risk_assessment.domain.take5.template import Take5Template


class RatingChoice(BaseModel):
    """The two choices a worker makes, with neither selected by default."""

    likelihood: str | None = None
    consequence: str | None = None


class ControlDraft(BaseModel):
    """A control while its description or kind may still be missing."""

    description: str = ""
    kind: ControlKind | None = None


class HazardDraft(BaseModel):
    """A hazard while the worker is filling in its ratings and controls."""

    description: str = ""
    before: RatingChoice = Field(default_factory=RatingChoice)
    controls: tuple[ControlDraft, ...] = ()
    after: RatingChoice = Field(default_factory=RatingChoice)


class Take5Draft(BaseModel):
    """Unsaved worker input; scores and bands are never accepted from the phone."""

    worker_name: str = ""
    job: str = ""
    location: str = ""
    hazards: tuple[HazardDraft, ...] = ()


class FieldError(BaseModel):
    """A message and the field it belongs beside, using a dotted field path."""

    path: str
    message: str


class DraftCheck(BaseModel):
    """The form errors, and the scoring model only when every field is valid."""

    errors: tuple[FieldError, ...]
    assessment: Take5 | None
    can_submit: bool


def _required_text(value: str, path: str, errors: list[FieldError]) -> str:
    """Trim an answer and report a blank field without discarding other errors."""
    cleaned: str = value.strip()
    if not cleaned:
        errors.append(FieldError(path=path, message="Fill in this field."))
    return cleaned


def _rating(
    choice: RatingChoice, template: Take5Template, path: str, errors: list[FieldError]
) -> RiskRating | None:
    """Validate both scale choices, then ask the matrix for the score and band."""
    for field, picked, scale in (
        ("likelihood", choice.likelihood, template.matrix.likelihoods),
        ("consequence", choice.consequence, template.matrix.consequences),
    ):
        if picked not in scale:
            errors.append(
                FieldError(path=f"{path}.{field}", message=f"Pick a {field}.")
            )
    if (
        choice.likelihood not in template.matrix.likelihoods
        or choice.consequence not in template.matrix.consequences
    ):
        return None
    assert choice.likelihood is not None and choice.consequence is not None
    return rate(template.matrix, choice.likelihood, choice.consequence)


def _hazard(
    draft: HazardDraft, template: Take5Template, path: str, errors: list[FieldError]
) -> Hazard | None:
    """Check one hazard and reuse the before rating when no controls were listed."""
    error_count: int = len(errors)
    description: str = _required_text(draft.description, f"{path}.description", errors)
    before: RiskRating | None = _rating(
        draft.before, template, f"{path}.before", errors
    )
    controls: list[Control] = []
    for index, control in enumerate(draft.controls):
        prefix: str = f"{path}.controls.{index}"
        wording: str = _required_text(
            control.description, f"{prefix}.description", errors
        )
        if control.kind is None:
            errors.append(
                FieldError(path=f"{prefix}.kind", message="Pick a control kind.")
            )
        elif wording:
            controls.append(Control(description=wording, kind=control.kind))
    after: RiskRating | None = (
        _rating(draft.after, template, f"{path}.after", errors)
        if draft.controls
        else before
    )
    if len(errors) != error_count or before is None or after is None:
        return None
    try:
        return Hazard(
            description=description,
            before=before,
            controls=tuple(controls),
            after=after,
        )
    except ValidationError as error:
        message: str = error.errors(include_context=False)[0]["msg"].removeprefix(
            "Value error, "
        )
        errors.append(FieldError(path=f"{path}.after", message=message))
        return None


def check_draft(draft: Take5Draft, template: Take5Template) -> DraftCheck:
    """Check all fields in one pass, returning errors without saving anything."""
    errors: list[FieldError] = []
    for field, value in (
        ("worker_name", draft.worker_name),
        ("job", draft.job),
        ("location", draft.location),
    ):
        _required_text(value, field, errors)
    if not draft.hazards:
        errors.append(FieldError(path="hazards", message="List at least one hazard."))
    hazards: list[Hazard] = []
    for index, draft_hazard in enumerate(draft.hazards):
        hazard: Hazard | None = _hazard(
            draft_hazard, template, f"hazards.{index}", errors
        )
        if hazard is not None:
            hazards.append(hazard)
    assessment: Take5 | None = (
        Take5(template=template, hazards=tuple(hazards)) if not errors else None
    )
    return DraftCheck(
        errors=tuple(errors), assessment=assessment, can_submit=not errors
    )
