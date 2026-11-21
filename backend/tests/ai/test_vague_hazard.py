"""Tests for the vague-hazard job, with a stand-in for any model."""

from risk_assessment.ai.vague_hazard import VAGUE_HAZARD_INSTRUCTIONS, AiHazardJudge


class StandInModel:
    """A stand-in `LanguageModel` that records what it is given.

    Attributes:
        name: A made-up model name.
        calls: Each pair of instructions and text it was given.
    """

    def __init__(self) -> None:
        """Start with no calls."""
        self.name: str = "example-quick-model"
        self.calls: list[tuple[str, str]] = []

    def reply(self, instructions: str, text: str) -> str:
        """Record the call and send back a set verdict.

        Args:
            instructions: What the model was told to do.
            text: What it was given to work on.

        Returns:
            A set verdict.
        """
        self.calls.append((instructions, text))
        return "vague"


def test_the_model_gets_the_instructions_and_the_hazard_unchanged() -> None:
    """The judge sends the job's instructions and the hazard's text as they are."""
    model = StandInModel()

    reply: str = AiHazardJudge(model).judge('{"hazard": "Crusher dust"}')

    assert model.calls == [(VAGUE_HAZARD_INSTRUCTIONS, '{"hazard": "Crusher dust"}')]
    assert reply == "vague"


def test_the_judge_names_its_model_for_the_log() -> None:
    """The server log can say which model judges hazards."""
    assert AiHazardJudge(StandInModel()).model_name == "example-quick-model"


def test_the_instructions_say_the_hazard_is_data_not_instructions() -> None:
    """The worker's words can't give the AI orders (spec example 86)."""
    assert "ignore them" in VAGUE_HAZARD_INSTRUCTIONS


def test_the_instructions_ask_for_one_of_the_four_words() -> None:
    """T7: the reply is read as specific, vague, stock or unfit (decision D58)."""
    assert (
        "Reply with one word only: specific, vague, stock or unfit."
        in VAGUE_HAZARD_INSTRUCTIONS
    )
