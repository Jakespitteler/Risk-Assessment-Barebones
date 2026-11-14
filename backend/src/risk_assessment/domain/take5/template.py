"""The Take 5 booklet's card.

A template holds the card's name, its questions, its risk matrix and the guidance
printed beside the scales.
"""

from typing import ClassVar, Self

from pydantic import BaseModel, ConfigDict, model_validator

from risk_assessment.domain.questions import Question, QuestionRole
from risk_assessment.domain.risk import RiskCell, RiskMatrix


class LevelGuidance(BaseModel):
    """What one level of a scale means, in the card's own words.

    Attributes:
        level: The level, such as "Rare".
        meaning: What it means, such as "Could happen, but only in rare cases".
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    level: str
    meaning: str


class Take5Template(BaseModel):
    """The card a Take 5 is filled in on. Each saved Take 5 keeps a copy of it.

    Attributes:
        name: The card's name, such as "Take 5 booklet".
        questions: The card's questions, in the order it prints them. Empty for a
            Take 5 saved before the app asked them.
        matrix: The risk matrix the hazards are rated on.
        likelihood_guidance: What each likelihood means, shown beside the rating.
        consequence_guidance: What each consequence means, shown beside the rating.
        control_guidance: What makes a control strong or weak, shown beside the
            controls.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    name: str
    questions: tuple[Question, ...] = ()
    matrix: RiskMatrix
    likelihood_guidance: tuple[LevelGuidance, ...] = ()
    consequence_guidance: tuple[LevelGuidance, ...] = ()
    control_guidance: str = ""

    @model_validator(mode="after")
    def _question_ids_are_unique(self) -> Self:
        """Refuse a card with two questions under one ID, since answers use the ID."""
        question_ids: list[str] = [question.id for question in self.questions]
        if len(question_ids) != len(set(question_ids)):
            raise ValueError("Every question on a card needs its own ID.")
        return self


_BOOKLET_LIKELIHOODS: tuple[str, ...] = (
    "Almost Certain",
    "Likely",
    "Possible",
    "Unlikely",
    "Rare",
)
_BOOKLET_CONSEQUENCES: tuple[str, ...] = (
    "Low",
    "Minor",
    "Moderate",
    "Major",
    "Critical",
)

# The score of each cell, one row per likelihood above. Unlikely / Critical is 19, not
# the 18 printed on the card; see docs/decisions.md.
_BOOKLET_SCORES: tuple[tuple[int, ...], ...] = (
    (11, 16, 20, 23, 25),
    (7, 12, 17, 21, 24),
    (4, 8, 13, 18, 22),
    (2, 5, 9, 14, 19),
    (1, 3, 6, 10, 15),
)

# Each band's name with its lowest and highest score (spec R2).
_BOOKLET_BANDS: tuple[tuple[str, int, int], ...] = (
    ("Low", 1, 5),
    ("Moderate", 6, 9),
    ("High", 10, 17),
    ("Extreme", 18, 25),
)


def _booklet_band(score: int) -> str:
    """Name the booklet band that a score falls in."""
    return next(
        name for name, lowest, highest in _BOOKLET_BANDS if lowest <= score <= highest
    )


BOOKLET_MATRIX = RiskMatrix(
    likelihoods=_BOOKLET_LIKELIHOODS,
    consequences=_BOOKLET_CONSEQUENCES,
    cells=tuple(
        tuple(RiskCell(score=score, band=_booklet_band(score)) for score in row)
        for row in _BOOKLET_SCORES
    ),
    jha_threshold=11,
)

# The card's questions, word for word, with the short ID each answer is kept against.
_BOOKLET_STOP_QUESTIONS: tuple[tuple[str, str], ...] = (
    ("scope", "Do you understand the task scope?"),
    ("procedure", "Does a procedure exist?"),
    ("steps", "Do you understand the steps required to do the task?"),
    ("equipment", "Are tools and equipment in good order?"),
    ("ppe", "Do you have the correct PPE?"),
    ("permits", "Do you have the necessary permits?"),
    ("plan", "Have you got a clear plan in mind?"),
)
_BOOKLET_HAZARD_QUESTIONS: tuple[tuple[str, str], ...] = (
    ("guards", "Will I be operating equipment with the guards removed?"),
    (
        "vehicles",
        "Am I or others at risk from the operation of vehicles or mobile equipment?",
    ),
    ("hazardous_materials", "Does the task involve hazardous materials?"),
    (
        "isolation",
        "Will I be performing a task without a specific isolation procedure?",
    ),
    ("heights", "Will I be working at heights?"),
    ("nearby_activity", "Will I be impacted by other activity in the vicinity?"),
    ("other", "Other environmental and/or H&S hazards?"),
)
_BOOKLET_QUESTIONS: tuple[Question, ...] = (
    *(
        Question(id=question_id, text=text, role=QuestionRole.STOP)
        for question_id, text in _BOOKLET_STOP_QUESTIONS
    ),
    *(
        Question(id=question_id, text=text, role=QuestionRole.HAZARD)
        for question_id, text in _BOOKLET_HAZARD_QUESTIONS
    ),
)

# The card's own wording for each level. It explains the scales without suggesting
# answers.
_BOOKLET_LIKELIHOOD_GUIDANCE: tuple[LevelGuidance, ...] = (
    LevelGuidance(level="Almost Certain", meaning="Expected to happen: once a week."),
    LevelGuidance(level="Likely", meaning="May easily happen: once a month."),
    LevelGuidance(level="Possible", meaning="May happen: once every year."),
    LevelGuidance(
        level="Unlikely",
        meaning="May happen sometime: once every 10 years.",
    ),
    LevelGuidance(
        level="Rare",
        meaning="May happen in extreme circumstances: once every 100 years.",
    ),
)
_BOOKLET_CONSEQUENCE_GUIDANCE: tuple[LevelGuidance, ...] = (
    LevelGuidance(level="Low", meaning="First aid treatment."),
    LevelGuidance(level="Minor", meaning="Medical treatment."),
    LevelGuidance(
        level="Moderate",
        meaning="Classified injury: lost time or restricted work.",
    ),
    LevelGuidance(level="Major", meaning="Fatality or severe permanent disability."),
    LevelGuidance(
        level="Critical",
        meaning="Multiple fatalities, or health effects to more than 50 people.",
    ),
)
_BOOKLET_CONTROL_GUIDANCE: str = (
    "Remove, isolate and barricade are strong controls: a strong control still works "
    "on a bad day. Systems, behaviour and PPE are weak controls: they rely on every "
    "person getting it right every time."
)

BOOKLET_TEMPLATE = Take5Template(
    name="Take 5 booklet",
    questions=_BOOKLET_QUESTIONS,
    matrix=BOOKLET_MATRIX,
    likelihood_guidance=_BOOKLET_LIKELIHOOD_GUIDANCE,
    consequence_guidance=_BOOKLET_CONSEQUENCE_GUIDANCE,
    control_guidance=_BOOKLET_CONTROL_GUIDANCE,
)
