# /// script
# requires-python = ">=3.13"
# dependencies = ["risk-assessment"]
#
# [tool.uv.sources]
# risk-assessment = { path = "../backend", editable = true }
# ///
"""Ask the real AI whether twelve made-up hazards are vague, and measure it (spec T6).

It reads the key and the model from `backend/.env` or the environment, as the app
does (`TAKE5_AI_KEY`, `TAKE5_AI_HAZARD_MODEL`). Each call costs real money: twelve
small calls per model named.

Usage, from the repo root:

    uv run scripts/try_vague_hazard.py
    uv run scripts/try_vague_hazard.py claude-haiku-5-5 claude-sonnet-5-5

It prints a Markdown table: each hazard, what a person would expect, what the word
rule says, what the AI says, how long it took and what it cost.
"""

import logging
import sys
import time

from try_challenge import PRICES_PER_MILLION_TOKENS, TokenCounter, cost_in_cents

from risk_assessment.ai.providers.claude import QUICK_MODEL, ClaudeModel
from risk_assessment.ai.vague_hazard import AiHazardJudge
from risk_assessment.domain.questions import Answer, QuestionRole
from risk_assessment.domain.take5.draft import HazardDraft, Take5Draft
from risk_assessment.domain.take5.hazard_nudges import (
    HazardToJudge,
    HazardVerdict,
    hazard_judgement_text,
    hazard_verdict,
    hazards_to_judge,
)
from risk_assessment.domain.take5.template import BOOKLET_TEMPLATE
from risk_assessment.domain.wording import word_count
from risk_assessment.settings import Settings

# Made up, every one: a hazard, the question it is linked to, the job, where it is,
# and what a person reading it would expect. Short and long, specific and vague.
SAMPLE_HAZARDS: tuple[tuple[str, str, str, str, HazardVerdict], ...] = (
    (
        "Crusher dust",
        "hazardous_materials",
        "Clear the blocked chute under the crusher feeder",
        "Primary crusher, level 2",
        HazardVerdict.SPECIFIC,
    ),
    (
        "Wheel nuts under tension",
        "other",
        "Change the front left tyre on LV12",
        "Light vehicle workshop",
        HazardVerdict.SPECIFIC,
    ),
    (
        "Feeder starts while I'm in the chute",
        "isolation",
        "Clear the blocked chute under the crusher feeder",
        "Primary crusher, level 2",
        HazardVerdict.SPECIFIC,
    ),
    (
        "Hit by a haul truck at the crib hut crossing",
        "vehicles",
        "Walk over to the crib hut for smoko",
        "North pit",
        HazardVerdict.SPECIFIC,
    ),
    (
        "Fall from the trailer deck while strapping the load",
        "heights",
        "Strap down the pump on the trailer for the trip to the pit",
        "Laydown yard by the stores",
        HazardVerdict.SPECIFIC,
    ),
    (
        "Vehicles",
        "vehicles",
        "Check the tyre pressures on the light vehicles",
        "Go line",
        HazardVerdict.VAGUE,
    ),
    (
        "Get hit by a car",
        "vehicles",
        "Survey the pegs along the haul road",
        "South pit haul road",
        HazardVerdict.VAGUE,
    ),
    (
        "Chemicals",
        "hazardous_materials",
        "Top up the battery cells in the substation UPS",
        "Substation 4",
        HazardVerdict.VAGUE,
    ),
    (
        "Slips trips and falls",
        "other",
        "Clean up the spillage under the conveyor",
        "Conveyor CV03",
        HazardVerdict.VAGUE,
    ),
    (
        "Heat",
        "other",
        "Weld new teeth on the loader bucket",
        "Outside the heavy vehicle workshop",
        HazardVerdict.VAGUE,
    ),
    (
        "There are some hazards around here today",
        "nearby_activity",
        "Inspect the crest of the bench",
        "Pit 2, bench 7",
        HazardVerdict.VAGUE,
    ),
    (
        "Working near other people doing other jobs in the area",
        "nearby_activity",
        "Replace the light over the crib hut door",
        "North pit crib hut",
        HazardVerdict.VAGUE,
    ),
)


def linked_hazard(
    description: str,
    question_id: str,
    job: str,
    location: str,
) -> HazardToJudge:
    """Make one sample hazard, linked to its question's Yes, as the app would judge it.

    Args:
        description: The hazard.
        question_id: The hazard question it is linked to.
        job: What the job is.
        location: Where it is.

    Returns:
        The hazard, with its question.

    Raises:
        ValueError: When the sample wouldn't be judged at all.
    """
    answers: dict[str, Answer] = {
        question.id: Answer.YES if question.role is QuestionRole.STOP else Answer.NO
        for question in BOOKLET_TEMPLATE.questions
    } | {question_id: Answer.YES}
    draft = Take5Draft(
        worker_name="Sam Example",
        job=job,
        location=location,
        answers=answers,
        hazards=(HazardDraft(description=description, covers=(question_id,)),),
    )
    judged: tuple[HazardToJudge, ...] = hazards_to_judge(draft, BOOKLET_TEMPLATE)
    if not judged:
        raise ValueError(f"The sample '{description}' would not be judged.")
    return judged[0]


def word_rule(description: str) -> str:
    """Say what the word rule decides on its own (spec T6).

    Args:
        description: The hazard.

    Returns:
        "vague" or "specific".
    """
    minimum: int | None = BOOKLET_TEMPLATE.specific_hazard_words
    is_short: bool = minimum is not None and word_count(description) < minimum
    return HazardVerdict.VAGUE.value if is_short else HazardVerdict.SPECIFIC.value


def measure(model_name: str, api_key: str, counter: TokenCounter) -> list[str]:
    """Ask one model about every sample, and write a table row for each.

    Args:
        model_name: The Claude model to ask.
        api_key: The key for Anthropic's API.
        counter: Where the adapter's token counts are added up.

    Returns:
        The table's rows for this model.
    """
    judge = AiHazardJudge(ClaudeModel(api_key, model_name))
    prices: tuple[float, float] | None = PRICES_PER_MILLION_TOKENS.get(model_name)
    rows: list[str] = []
    for description, question_id, job, location, expected in SAMPLE_HAZARDS:
        hazard: HazardToJudge = linked_hazard(description, question_id, job, location)
        counter.input_tokens = counter.output_tokens = 0
        started: float = time.perf_counter()
        try:
            reply: str = judge.judge(hazard_judgement_text(hazard, job, location))
        except Exception as error:  # Show every failure in the table.
            reply = f"(failed: {type(error).__name__})"
        seconds: float = time.perf_counter() - started
        verdict: HazardVerdict | None = hazard_verdict(reply)
        says: str = verdict.value if verdict else f"unusable: {reply.strip()}"
        rows.append(
            f"| {model_name} | {description} | {job} | {expected.value} "
            f"| {word_rule(description)} | {says} | {seconds:.1f} s "
            f"| {counter.input_tokens} / {counter.output_tokens} "
            f"| {cost_in_cents(counter, prices)} |",
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
    model_names: list[str] = sys.argv[1:] or [settings.ai_hazard_model or QUICK_MODEL]
    counter = TokenCounter()
    logging.getLogger("risk_assessment.ai.providers.claude").addHandler(counter)
    logging.getLogger("risk_assessment.ai.providers.claude").setLevel(logging.INFO)
    print(
        "| Model | Hazard | Job | A person expects | Word rule | AI says | Time "
        "| Tokens in / out | Cost |",
    )
    print("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for model_name in model_names:
        for row in measure(model_name, api_key, counter):
            print(row, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
