"""Tests for ranking Take 5s worst first (spec W1 to W6), from the worked examples."""

import json
from datetime import UTC, datetime, timedelta
from typing import Any

from risk_assessment.domain.risk import rate
from risk_assessment.domain.take5.challenge import AskedBy, Challenge
from risk_assessment.domain.take5.ranking import (
    RankedBy,
    RankedTake5,
    checked_ai_order,
    rank_by_rules,
    ranking_text,
    rule_line,
    with_ai_order,
    worst_score,
)
from risk_assessment.domain.take5.saved import SavedTake5
from risk_assessment.domain.take5.take5 import Hazard
from risk_assessment.domain.take5.template import BOOKLET_MATRIX
from tests.samples import BARRICADE, sample_saved_take5

SAVED_AT: datetime = datetime(2026, 11, 20, 7, 30, tzinfo=UTC)
CAREFUL_HAZARD: str = "Wheel rolls off the hub and crushes a foot"
CAREFUL_ANSWER: str = "Wheels chocked both sides and nuts torqued"


def ranked_take5(
    description: str = CAREFUL_HAZARD,
    before: tuple[str, str] = ("Possible", "Minor"),
    after: tuple[str, str] = ("Unlikely", "Minor"),
    answer: str | None = CAREFUL_ANSWER,
    minutes_taken: float | None = 10,
    saved_at: datetime = SAVED_AT,
) -> SavedTake5:
    """Make the worked examples' Take 5: careful answers, 10 minutes, 8 then 5.

    Args:
        description: The one hazard's description.
        before: Its likelihood and consequence before controls.
        after: Its likelihood and consequence after a barricade.
        answer: The answer to the question, or None for an unfinished Take 5.
        minutes_taken: Minutes from starting to saving, or None for no start time.
        saved_at: When it was saved.

    Returns:
        The saved Take 5.
    """
    sample: SavedTake5 = sample_saved_take5()
    unfinished: bool = answer is None
    return sample.model_copy(
        update={
            "hazards": (
                Hazard(
                    description=description,
                    before=rate(BOOKLET_MATRIX, *before),
                    controls=(BARRICADE,),
                    after=rate(BOOKLET_MATRIX, *after),
                ),
            ),
            "created_at": saved_at,
            "started_at": (
                None
                if minutes_taken is None
                else saved_at - timedelta(minutes=minutes_taken)
            ),
            "challenge": Challenge(
                question="What has to go right?",
                asked_by=AskedBy.FALLBACK,
                answer=answer,
            ),
            "verdict": None if unfinished else sample.verdict,
            "finished_at": None if unfinished else saved_at,
        },
    )


def test_example_88_careful_answers_score_the_highest_risk_alone() -> None:
    """W1: with no thought gaps, the score is the highest before-controls score."""
    take5: SavedTake5 = ranked_take5()

    assert worst_score(take5) == 8
    assert rule_line(take5) == "Highest risk 8 Moderate. No signs of a rushed Take 5."


def test_example_89_a_hazard_under_six_words_adds_five() -> None:
    """W2: a hazard in fewer than 6 words is a thought gap."""
    take5: SavedTake5 = ranked_take5(description="Moving wheel")

    assert worst_score(take5) == 13
    assert rule_line(take5) == (
        "Highest risk 8 Moderate. “Moving wheel” is under 6 words."
    )


def test_example_90_controls_that_leave_the_risk_unchanged_add_five() -> None:
    """W3: controls that don't lower a hazard's score are a thought gap."""
    take5: SavedTake5 = ranked_take5(after=("Possible", "Minor"))

    assert worst_score(take5) == 13
    assert "don't lower its risk" in rule_line(take5)


def test_example_91_an_unanswered_question_adds_five() -> None:
    """W4: a Take 5 whose question was never answered has a thought gap."""
    take5: SavedTake5 = ranked_take5(answer=None)

    assert worst_score(take5) == 13
    assert rule_line(take5).endswith("The question was never answered.")


def test_example_92_a_four_word_answer_adds_five() -> None:
    """W4: an answer in fewer than 6 words is a thought gap, though C4 accepts it."""
    take5: SavedTake5 = ranked_take5(answer="Wheels chocked both sides")

    assert worst_score(take5) == 13


def test_example_93_a_take5_saved_inside_two_minutes_is_rushed() -> None:
    """W5: started 1 minute 59 seconds before it was saved is rushed."""
    take5: SavedTake5 = ranked_take5(minutes_taken=119 / 60)

    assert worst_score(take5) == 13
    assert rule_line(take5).endswith("It was filled in in under 2 minutes.")


def test_example_94_exactly_two_minutes_is_not_rushed() -> None:
    """W5: exactly 2 minutes is on the boundary, so not rushed."""
    assert worst_score(ranked_take5(minutes_taken=2)) == 8


def test_example_95_no_start_time_is_never_rushed() -> None:
    """W5: a Take 5 saved before start times were kept can't be judged rushed."""
    assert worst_score(ranked_take5(minutes_taken=None)) == 8


def test_example_96_equal_scores_put_the_newest_first() -> None:
    """W1: a tie goes to the one saved last."""
    risky_but_careful: SavedTake5 = ranked_take5(before=("Possible", "Major"))
    rushed_and_short: SavedTake5 = ranked_take5(
        description="Moving wheel",
        minutes_taken=1,
        saved_at=SAVED_AT + timedelta(minutes=5),
    )

    ranked: tuple[RankedTake5, ...] = rank_by_rules(
        (risky_but_careful, rushed_and_short),
    )

    assert [each.score for each in ranked] == [18, 18]
    assert [each.take5.id for each in ranked] == [
        rushed_and_short.id,
        risky_but_careful.id,
    ]


def test_example_97_little_thought_outranks_higher_risk() -> None:
    """W1: three thought gaps on an 8 outweigh a careful 18."""
    risky_but_careful: SavedTake5 = ranked_take5(before=("Possible", "Major"))
    careless: SavedTake5 = ranked_take5(
        description="Moving wheel",
        answer=None,
        minutes_taken=1,
    )

    ranked: tuple[RankedTake5, ...] = rank_by_rules((risky_but_careful, careless))

    assert [each.score for each in ranked] == [23, 18]
    assert ranked[0].take5.id == careless.id
    assert all(each.ranked_by is RankedBy.RULES for each in ranked)


def test_each_short_hazard_counts_on_its_own() -> None:
    """W2: two short hazards are two thought gaps."""
    take5: SavedTake5 = ranked_take5(description="Moving wheel")
    second: Hazard = take5.hazards[0].model_copy(update={"description": "Jack"})
    two_short: SavedTake5 = take5.model_copy(
        update={"hazards": (*take5.hazards, second)},
    )

    assert worst_score(two_short) == 18


def test_the_ai_is_given_numbers_and_never_the_workers_name() -> None:
    """W6: the AI gets each Take 5 numbered, with its answer, but no name."""
    worst: tuple[RankedTake5, ...] = rank_by_rules(
        (ranked_take5(), ranked_take5(answer=None)),
    )

    text: str = ranking_text(worst)
    given: dict[str, Any] = json.loads(text)

    assert [each["number"] for each in given["take5s"]] == [1, 2]
    assert given["take5s"][0]["answer"] is None
    assert given["take5s"][1]["answer"] == CAREFUL_ANSWER
    assert given["take5s"][1]["minutes_taken"] == 10
    assert "Sam Example" not in text


def test_example_98_an_ai_reply_that_repeats_a_number_is_thrown_away() -> None:
    """W6: a reply must hold each number exactly once."""
    reply: str = json.dumps(
        {"ranking": [{"number": 1, "why": "Short."}, {"number": 1, "why": "Again."}]},
    )

    assert checked_ai_order(reply, 2) is None


def test_ai_replies_that_fail_the_checks_are_thrown_away() -> None:
    """W6: not JSON, a missing number, an empty, long or two-line reason all fail."""
    long_line: str = "x" * 201
    replies: list[str] = [
        "The first one is worst.",
        json.dumps({"ranking": [{"number": 1, "why": "Only one."}]}),
        json.dumps(
            {"ranking": [{"number": 2, "why": " "}, {"number": 1, "why": "Fine."}]},
        ),
        json.dumps(
            {
                "ranking": [
                    {"number": 2, "why": long_line},
                    {"number": 1, "why": "Fine."},
                ],
            },
        ),
        json.dumps(
            {
                "ranking": [
                    {"number": 2, "why": "Two\nlines."},
                    {"number": 1, "why": "Fine."},
                ],
            },
        ),
    ]

    assert [checked_ai_order(reply, 2) for reply in replies] == [None] * 5


def test_the_ai_order_is_used_for_the_worst_and_the_rest_follow() -> None:
    """W6: the AI reorders the Take 5s it was given; the others stay in rule order."""
    ranked: tuple[RankedTake5, ...] = rank_by_rules(
        (
            ranked_take5(answer=None, minutes_taken=1),
            ranked_take5(answer=None),
            ranked_take5(),
        ),
    )
    reply: str = json.dumps(
        {
            "ranking": [
                {"number": 2, "why": "The answer dodges the question."},
                {"number": 1, "why": "Rushed."},
            ],
        },
    )
    order: tuple[tuple[int, str], ...] | None = checked_ai_order(reply, 2)
    assert order is not None

    reordered: tuple[RankedTake5, ...] = with_ai_order(ranked, order)

    assert [each.take5.id for each in reordered] == [
        ranked[1].take5.id,
        ranked[0].take5.id,
        ranked[2].take5.id,
    ]
    assert [each.ranked_by for each in reordered] == [
        RankedBy.AI,
        RankedBy.AI,
        RankedBy.RULES,
    ]
    assert reordered[0].line == "The answer dodges the question."


def test_example_99_an_ai_line_naming_the_worker_gets_the_rule_line() -> None:
    """W6: a line naming the worker is replaced by the rule line."""
    ranked: tuple[RankedTake5, ...] = rank_by_rules(
        (ranked_take5(answer=None), ranked_take5()),
    )
    reply: str = json.dumps(
        {
            "ranking": [
                {"number": 1, "why": "Sam Example skipped the question."},
                {"number": 2, "why": "Careful."},
            ],
        },
    )
    order: tuple[tuple[int, str], ...] | None = checked_ai_order(reply, 2)
    assert order is not None

    reordered: tuple[RankedTake5, ...] = with_ai_order(ranked, order)

    assert reordered[0].line == ranked[0].line
    assert reordered[0].ranked_by is RankedBy.RULES
    assert reordered[1].line == "Careful."
