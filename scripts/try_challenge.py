# /// script
# requires-python = ">=3.13"
# dependencies = ["risk-assessment"]
#
# [tool.uv.sources]
# risk-assessment = { path = "../backend", editable = true }
# ///
"""Ask the real AI for the challenge question on five made-up Take 5s, and measure it.

It reads the key and the model from `backend/.env` or the environment, as the app
does (`TAKE5_AI_KEY`, `TAKE5_AI_MODEL`). Each call costs real money: about five
questions per model named.

Usage, from the repo root:

    uv run scripts/try_challenge.py
    uv run scripts/try_challenge.py claude-opus-5-5 claude-sonnet-5-5 claude-haiku-5-5

It prints a Markdown table: each question, whether it passed the check (spec C2),
how long it took and what it cost.
"""

import logging
import sys
import time

from risk_assessment.ai.challenge import AiChallengeAsker
from risk_assessment.ai.providers.claude import ClaudeModel
from risk_assessment.domain.controls import ControlKind
from risk_assessment.domain.questions import Answer, QuestionRole
from risk_assessment.domain.take5.challenge import challenge_text, checked_question
from risk_assessment.domain.take5.draft import (
    ControlDraft,
    DraftCheck,
    HazardDraft,
    RatingChoice,
    Take5Draft,
    check_draft,
)
from risk_assessment.domain.take5.template import BOOKLET_TEMPLATE
from risk_assessment.settings import Settings

# US dollars per million input and output tokens, from Anthropic's price list.
PRICES_PER_MILLION_TOKENS: dict[str, tuple[float, float]] = {
    "claude-opus-5-5": (4.00, 20.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-haiku-5-5": (0.10, 0.50),
}


class TokenCounter(logging.Handler):
    """Adds up the tokens the Claude adapter logs for each reply.

    Attributes:
        input_tokens: The input tokens since the count was last reset.
        output_tokens: The output tokens, thinking included, since then.
    """

    def __init__(self) -> None:
        """Start counting from nothing."""
        super().__init__()
        self.input_tokens: int = 0
        self.output_tokens: int = 0

    def emit(self, record: logging.LogRecord) -> None:
        """Add one reply's tokens.

        Args:
            record: A log line from the adapter.
        """
        self.input_tokens += int(getattr(record, "input_tokens", 0))
        self.output_tokens += int(getattr(record, "output_tokens", 0))


def answers(**changed: Answer) -> dict[str, Answer]:
    """Answer every think-through question Yes and every hazard question No.

    Args:
        **changed: Answers to change, by question ID.

    Returns:
        One answer for each of the booklet's questions.
    """
    default_answers: dict[str, Answer] = {
        question.id: Answer.YES if question.role is QuestionRole.STOP else Answer.NO
        for question in BOOKLET_TEMPLATE.questions
    }
    return default_answers | changed


def hazard(
    description: str,
    before: tuple[str, str],
    after: tuple[str, str],
    *controls: tuple[str, ControlKind],
    covers: tuple[str, ...] = (),
    weak_controls_reason: str = "",
) -> HazardDraft:
    """Make one hazard as the phone sends it.

    Args:
        description: The hazard.
        before: The likelihood and consequence before controls.
        after: The likelihood and consequence after controls.
        *controls: Each control's words and kind.
        covers: The hazard questions it is linked to.
        weak_controls_reason: Why no strong control is possible, when T3 asks.

    Returns:
        The hazard.
    """
    return HazardDraft(
        description=description,
        before=RatingChoice(likelihood=before[0], consequence=before[1]),
        controls=tuple(
            ControlDraft(description=words, kind=kind) for words, kind in controls
        ),
        after=RatingChoice(likelihood=after[0], consequence=after[1]),
        covers=covers,
        weak_controls_reason=weak_controls_reason,
    )


# Made up, every one. Each has a different weak spot for the AI to find.
SAMPLE_TAKE5S: tuple[Take5Draft, ...] = (
    Take5Draft(
        worker_name="Sam Example",
        job="Change the front left tyre on LV12",
        location="Workshop bay 3",
        answers=answers(),
        hazards=(
            hazard(
                "Wheel falls off the jack onto my legs",
                ("Possible", "Major"),
                ("Rare", "Major"),
                ("Use the workshop jack", ControlKind.SYSTEMS),
                ("Wear steel cap boots", ControlKind.PPE),
                weak_controls_reason="No stands in the bay today",
            ),
        ),
    ),
    Take5Draft(
        worker_name="Sam Example",
        job="Strap down the pump on the trailer for the trip to the pit",
        location="Laydown yard by the stores",
        answers=answers(),
        hazards=(
            hazard(
                "Ratchet strap snaps and whips back at my face",
                ("Unlikely", "Moderate"),
                ("Rare", "Moderate"),
                ("Check the straps for cuts before using them", ControlKind.SYSTEMS),
            ),
        ),
    ),
    Take5Draft(
        worker_name="Sam Example",
        job="Clear the blocked chute under the crusher feeder",
        location="Primary crusher, level 2",
        answers=answers(isolation=Answer.YES),
        hazards=(
            hazard(
                "Feeder starts up while I am clearing the chute",
                ("Possible", "Major"),
                ("Rare", "Major"),
                ("Lock out the feeder at the MCC", ControlKind.ISOLATE),
                covers=("isolation",),
            ),
            hazard(
                "Crusher dust in my lungs",
                ("Possible", "Minor"),
                ("Unlikely", "Minor"),
                ("P2 mask", ControlKind.PPE),
            ),
        ),
    ),
    Take5Draft(
        worker_name="Sam Example",
        job="Replace the light over the crib hut door",
        location="North pit crib hut",
        answers=answers(heights=Answer.YES),
        hazards=(
            hazard(
                "Fall off the ladder onto the concrete",
                ("Possible", "Major"),
                ("Unlikely", "Moderate"),
                ("Keep three points of contact", ControlKind.BEHAVIOUR),
                covers=("heights",),
                weak_controls_reason="The EWP is booked out all week",
            ),
        ),
    ),
    Take5Draft(
        worker_name="Sam Example",
        job="Top up the battery cells in the substation UPS",
        location="Substation 4",
        answers=answers(permits=Answer.NO, hazardous_materials=Answer.YES),
        hazards=(
            hazard(
                "Battery acid splashed in my eyes",
                ("Possible", "Moderate"),
                ("Unlikely", "Minor"),
                ("Face shield and acid gloves", ControlKind.PPE),
                covers=("hazardous_materials",),
                weak_controls_reason="You have to handle the acid to top it up",
            ),
        ),
    ),
)


def sample_texts() -> list[tuple[str, str]]:
    """Check and rate each sample, and write it out as the AI is given it.

    Returns:
        Each sample's job and the text sent to the AI.

    Raises:
        ValueError: When a sample has a gap, so it couldn't be submitted.
    """
    texts: list[tuple[str, str]] = []
    for draft in SAMPLE_TAKE5S:
        check: DraftCheck = check_draft(draft, BOOKLET_TEMPLATE)
        if check.assessment is None:
            raise ValueError(f"The sample '{draft.job}' has gaps: {check.errors}")
        texts.append(
            (draft.job, challenge_text(check.assessment, draft.job, draft.location)),
        )
    return texts


def cost_in_cents(counter: TokenCounter, prices: tuple[float, float] | None) -> str:
    """Work out what one reply cost, from its tokens and the model's prices.

    Args:
        counter: The reply's input and output tokens.
        prices: US dollars per million input and output tokens, or None when the
            model isn't in `PRICES_PER_MILLION_TOKENS`.

    Returns:
        The cost in US cents, or "price unknown", so a missing price never shows
        as a cost of nothing.
    """
    if prices is None:
        return "price unknown"
    input_price, output_price = prices
    cents: float = (
        counter.input_tokens * input_price + counter.output_tokens * output_price
    ) / 10_000
    return f"{cents:.2f}c"


def measure(model_name: str, api_key: str, counter: TokenCounter) -> list[str]:
    """Ask one model about every sample, and write a table row for each.

    Args:
        model_name: The Claude model to ask.
        api_key: The key for Anthropic's API.
        counter: Where the adapter's token counts are added up.

    Returns:
        The table's rows for this model.
    """
    asker = AiChallengeAsker(ClaudeModel(api_key, model_name))
    prices: tuple[float, float] | None = PRICES_PER_MILLION_TOKENS.get(model_name)
    rows: list[str] = []
    for job, text in sample_texts():
        counter.input_tokens = counter.output_tokens = 0
        started: float = time.perf_counter()
        try:
            question: str = asker.ask(text).text
        except Exception as error:  # Show every failure in the table.
            question = f"(failed: {type(error.__cause__ or error).__name__})"
        seconds: float = time.perf_counter() - started
        cost: str = cost_in_cents(counter, prices)
        passes: str = "yes" if checked_question(question) else "no"
        rows.append(
            f"| {model_name} | {job} | {question.strip()} | {passes} "
            f"| {seconds:.1f} s | {counter.input_tokens} / {counter.output_tokens} "
            f"| {cost} |",
        )
    return rows


def main() -> int:
    """Measure each model named on the command line, or the one in the settings.

    Returns:
        The exit code: 0, or 1 when no key is set.
    """
    settings = Settings()
    api_key: str | None = settings.usable_ai_key
    if api_key is None:
        print("Set TAKE5_AI_KEY in backend/.env first (see the README).")
        return 1
    model_names: list[str] = sys.argv[1:] or [settings.ai_model or "claude-opus-5-5"]
    counter = TokenCounter()
    logging.getLogger("risk_assessment.ai.providers.claude").addHandler(counter)
    logging.getLogger("risk_assessment.ai.providers.claude").setLevel(logging.INFO)
    print("| Model | Job | Question | Passes C2 | Time | Tokens in / out | Cost |")
    print("| --- | --- | --- | --- | --- | --- | --- |")
    for model_name in model_names:
        for row in measure(model_name, api_key, counter):
            print(row, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
