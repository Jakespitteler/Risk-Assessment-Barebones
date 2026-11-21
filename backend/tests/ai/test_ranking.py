"""Tests for the ranking job, with a stand-in for any model."""

from risk_assessment.ai.ranking import (
    BEST_INSTRUCTIONS,
    RANKING_INSTRUCTIONS,
    AiTake5Ranker,
)


class StandInModel:
    """A stand-in `LanguageModel` that records what it is given.

    Attributes:
        name: A made-up model name.
        calls: Each pair of instructions and text it was given.
    """

    def __init__(self) -> None:
        """Start with no calls."""
        self.name: str = "example-model"
        self.calls: list[tuple[str, str]] = []

    def reply(self, instructions: str, text: str) -> str:
        """Record the call and send back a set ranking.

        Args:
            instructions: What the model was told to do.
            text: What it was given to work on.

        Returns:
            A set ranking.
        """
        self.calls.append((instructions, text))
        return '{"ranking": []}'


def test_the_model_gets_the_instructions_and_the_take5s_unchanged() -> None:
    """The ranker sends the job's instructions and the Take 5s' text as they are."""
    model = StandInModel()

    reply: str = AiTake5Ranker(model).rank('{"take5s": []}')

    assert model.calls == [(RANKING_INSTRUCTIONS, '{"take5s": []}')]
    assert reply == '{"ranking": []}'


def test_the_model_gets_the_best_instructions_to_pick_the_best() -> None:
    """W8: picking the best sends its own instructions and the Take 5s as they are."""
    model = StandInModel()

    AiTake5Ranker(model).pick_best('{"take5s": []}')

    assert model.calls == [(BEST_INSTRUCTIONS, '{"take5s": []}')]
