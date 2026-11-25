"""Tests for plugging the AI named in the settings into the app."""

import logging
from pathlib import Path
from typing import cast

import anthropic
import openai
import pytest
from pydantic import SecretStr

from risk_assessment.ai.card_reader import AiCardReader
from risk_assessment.ai.challenge import AiChallengeAsker
from risk_assessment.ai.providers import chatgpt, claude
from risk_assessment.ai.ranking import AiTake5Ranker
from risk_assessment.ai.vague_hazard import AiHazardJudge
from risk_assessment.api.app import (
    build_card_reader,
    build_challenge_asker,
    build_hazard_judge,
    build_take5_ranker,
    create_app,
    missing_key_help,
)
from risk_assessment.domain.take5.ranking import AI_RANKING_TIME_LIMIT_SECONDS
from risk_assessment.domain.take5.template import BOOKLET_TEMPLATE
from risk_assessment.services.ports import (
    CardReader,
    ChallengeAsker,
    HazardJudge,
    Take5Ranker,
)
from risk_assessment.settings import AiProvider, Settings
from risk_assessment.storage.sqlite import SqliteTake5Repository
from tests.ai.fake_anthropic import FakeAnthropicApi
from tests.ai.fake_openai import FakeOpenAiApi


def test_with_no_key_no_ai_is_plugged_in() -> None:
    """No key means no asker, so the fixed question is asked (spec C3)."""
    assert build_challenge_asker(Settings(ai_key=None)) is None


def test_with_a_key_the_ai_asks_the_question() -> None:
    """A key plugs in the provider named in the settings. Nothing is sent yet."""
    asker: ChallengeAsker | None = build_challenge_asker(
        Settings(ai_key=SecretStr("made-up-key")),
    )

    assert isinstance(asker, AiChallengeAsker)


def test_with_no_key_the_fixed_rules_rank_alone() -> None:
    """No key means no ranker, so W1 orders the Take 5s alone (spec W6)."""
    assert build_take5_ranker(Settings(ai_key=None)) is None


def test_ranking_calls_may_take_as_long_as_the_ranking_waits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """W6 waits 20 seconds, so a ranking call isn't cut off at the usual 11."""
    timeouts: list[object] = []

    def record_client(**settings: object) -> object:
        """Stand in for Anthropic's client, keeping its time limit.

        Args:
            settings: What the client is set up with.

        Returns:
            Something in the client's place; nothing is sent.
        """
        timeouts.append(settings["timeout"])
        return object()

    monkeypatch.setattr(claude.anthropic, "Anthropic", record_client)

    ranker: Take5Ranker | None = build_take5_ranker(
        Settings(ai_key=SecretStr("made-up-key")),
    )

    assert isinstance(ranker, AiTake5Ranker)
    assert timeouts == [AI_RANKING_TIME_LIMIT_SECONDS + 1]


def test_with_no_key_the_word_rule_judges_hazards() -> None:
    """No key means no judge, so the word rule decides (spec T6)."""
    assert build_hazard_judge(Settings(ai_key=None)) is None


def test_hazards_are_judged_by_the_providers_quick_model() -> None:
    """With no hazard model set, Claude Haiku 5.5 judges hazards (decision D61)."""
    judge: HazardJudge | None = build_hazard_judge(
        Settings(ai_key=SecretStr("made-up-key"), ai_model="claude-opus-5-5"),
    )

    assert isinstance(judge, AiHazardJudge)
    assert judge.model_name == "claude-haiku-5-5"


def test_the_hazard_model_is_a_setting() -> None:
    """`TAKE5_AI_HAZARD_MODEL` picks another model for this job only."""
    judge: HazardJudge | None = build_hazard_judge(
        Settings(
            ai_key=SecretStr("made-up-key"),
            ai_hazard_model="claude-sonnet-5-5",
        ),
    )

    assert isinstance(judge, AiHazardJudge)
    assert judge.model_name == "claude-sonnet-5-5"


def test_the_log_names_the_model_that_asks(caplog: pytest.LogCaptureFixture) -> None:
    """With a key, one info line says which model writes the question."""
    with caplog.at_level(logging.INFO, logger="risk_assessment"):
        build_challenge_asker(
            Settings(ai_key=SecretStr("made-up-key"), ai_model="claude-haiku-5-5"),
        )

    assert "The challenge question is asked of claude-haiku-5-5." in caplog.messages


def test_the_app_lets_its_info_lines_reach_the_log(tmp_path: Path) -> None:
    """The app's info lines reach the log, so a developer sees the AI is on."""
    create_app(SqliteTake5Repository(tmp_path / "take5.sqlite3"))

    assert logging.getLogger("risk_assessment").isEnabledFor(logging.INFO)
    assert logging.getLogger("risk_assessment").handlers


def test_with_no_key_cards_are_not_scanned() -> None:
    """No key means no card reader, so scanning says it needs an AI (task 0033)."""
    assert build_card_reader(Settings(ai_key=None)) is None


def test_cards_are_read_by_the_main_model_at_medium_effort(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With no scan model set, the main model reads, thinking harder than usual."""
    api = FakeAnthropicApi(reply="{}")
    real_client = claude.anthropic.Anthropic

    def fake_client(**settings: object) -> anthropic.Anthropic:
        """Make Anthropic's client send every call to the stand-in API.

        Args:
            settings: What the client is set up with.

        Returns:
            A client that never reaches the network.
        """
        return real_client(
            api_key=cast(str, settings["api_key"]),
            max_retries=0,
            http_client=api.http_client(),
        )

    monkeypatch.setattr(claude.anthropic, "Anthropic", fake_client)
    reader: CardReader | None = build_card_reader(
        Settings(ai_key=SecretStr("made-up-key"), ai_model="claude-sonnet-5-5"),
    )
    assert reader is not None

    reader.read(b"photo", "image/jpeg", BOOKLET_TEMPLATE)

    assert api.requests[0]["model"] == "claude-sonnet-5-5"
    assert api.requests[0]["output_config"] == {"effort": "medium"}


def test_the_scan_model_is_a_setting() -> None:
    """`TAKE5_AI_SCAN_MODEL` picks another model for reading cards only."""
    reader: CardReader | None = build_card_reader(
        Settings(
            ai_key=SecretStr("made-up-key"),
            ai_model="claude-sonnet-5-5",
            ai_scan_model="claude-fable-5-2",
        ),
    )

    assert isinstance(reader, AiCardReader)
    assert reader.model_name == "claude-fable-5-2"


CHATGPT_KEY: SecretStr = SecretStr("made-up-key")


def test_chatgpt_does_every_ai_job_when_it_is_chosen(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """`TAKE5_AI_PROVIDER=chatgpt` plugs OpenAI's models into every job (0045)."""
    settings = Settings(ai_provider=AiProvider.CHATGPT, ai_key=CHATGPT_KEY)

    with caplog.at_level(logging.INFO, logger="risk_assessment"):
        asker: ChallengeAsker | None = build_challenge_asker(settings)
        ranker: Take5Ranker | None = build_take5_ranker(settings)
    judge: HazardJudge | None = build_hazard_judge(settings)
    reader: CardReader | None = build_card_reader(settings)

    assert isinstance(asker, AiChallengeAsker)
    assert isinstance(ranker, AiTake5Ranker)
    assert f"The challenge question is asked of {chatgpt.DEFAULT_MODEL}." in (
        caplog.messages
    )
    assert f"Take 5s are ranked by {chatgpt.DEFAULT_MODEL}." in caplog.messages
    assert isinstance(judge, AiHazardJudge)
    assert judge.model_name == chatgpt.QUICK_MODEL
    assert isinstance(reader, AiCardReader)
    assert reader.model_name == chatgpt.DEFAULT_MODEL


def test_chatgpt_reads_cards_at_medium_effort(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reading handwriting thinks harder than usual with ChatGPT too (task 0045)."""
    api = FakeOpenAiApi(reply="{}")
    real_client = chatgpt.openai.OpenAI

    def fake_client(**settings: object) -> openai.OpenAI:
        """Make OpenAI's client send every call to the stand-in API.

        Args:
            settings: What the client is set up with.

        Returns:
            A client that never reaches the network.
        """
        return real_client(
            api_key=cast(str, settings["api_key"]),
            max_retries=0,
            http_client=api.http_client(),
        )

    monkeypatch.setattr(chatgpt.openai, "OpenAI", fake_client)
    reader: CardReader | None = build_card_reader(
        Settings(ai_provider=AiProvider.CHATGPT, ai_key=CHATGPT_KEY),
    )
    assert reader is not None

    reader.read(b"photo", "image/jpeg", BOOKLET_TEMPLATE)

    assert api.requests[0]["model"] == chatgpt.DEFAULT_MODEL
    assert api.requests[0]["reasoning"] == {"effort": "medium"}


@pytest.mark.parametrize(
    ("provider", "key_page"),
    [
        (AiProvider.CLAUDE, "https://console.anthropic.com/settings/keys"),
        (AiProvider.CHATGPT, "https://platform.openai.com/api-keys"),
    ],
)
def test_with_no_key_the_log_says_how_to_set_one(
    provider: AiProvider,
    key_page: str,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The warning names the provider's key page and the command, on its own line."""
    with caplog.at_level(logging.WARNING, logger="risk_assessment"):
        create_app(
            settings=Settings(
                ai_key=SecretStr("  "),
                ai_provider=provider,
                database_path=tmp_path / "take5.sqlite3",
            ),
        )

    assert caplog.messages == [missing_key_help(provider)]
    assert key_page in caplog.messages[0]
    assert "    uv run set_ai_key.py\n" in caplog.messages[0]


def test_with_a_key_the_log_asks_for_none(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A set key means no warning about it."""
    with caplog.at_level(logging.WARNING, logger="risk_assessment"):
        create_app(
            settings=Settings(
                ai_key=SecretStr("made-up-key"),
                database_path=tmp_path / "take5.sqlite3",
            ),
        )

    assert "set_ai_key" not in caplog.text
