"""Tests for reading the settings from the environment."""

from pathlib import Path

import pytest

from risk_assessment.settings import AiProvider, Settings


def test_the_database_is_in_the_ignored_data_folder_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With nothing set, the database is `backend/.data/take5.sqlite3`."""
    monkeypatch.delenv("TAKE5_DATABASE_PATH", raising=False)

    database_path: Path = Settings().database_path

    assert database_path.parts[-3:] == ("backend", ".data", "take5.sqlite3")


def test_the_database_path_can_be_set_from_the_environment(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """`TAKE5_DATABASE_PATH` moves the database."""
    monkeypatch.setenv("TAKE5_DATABASE_PATH", str(tmp_path / "other.sqlite3"))

    assert Settings().database_path == tmp_path / "other.sqlite3"


def test_with_no_ai_key_there_is_no_usable_key() -> None:
    """An empty `TAKE5_AI_KEY` (set by the tests' set-up) means no AI."""
    assert Settings().usable_ai_key is None


def test_an_ai_key_of_only_spaces_is_no_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """A key that is only spaces is treated as not set."""
    monkeypatch.setenv("TAKE5_AI_KEY", "   ")

    assert Settings().usable_ai_key is None


def test_the_ai_settings_can_be_set_from_the_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The provider, model and key each have a `TAKE5_` variable."""
    monkeypatch.setenv("TAKE5_AI_PROVIDER", "claude")
    monkeypatch.setenv("TAKE5_AI_MODEL", "claude-example")
    monkeypatch.setenv("TAKE5_AI_KEY", " made-up-key ")

    settings = Settings()

    assert settings.ai_provider == AiProvider.CLAUDE
    assert settings.ai_model == "claude-example"
    assert settings.usable_ai_key == "made-up-key"


def test_the_ai_key_can_be_kept_in_a_local_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A key in a `.env` file is read when no environment variable is set."""
    monkeypatch.delenv("TAKE5_AI_KEY")
    local_settings_file: Path = tmp_path / ".env"
    local_settings_file.write_text("TAKE5_AI_KEY=made-up-key\nOTHER=1\n")

    # pydantic-settings takes `_env_file`, but its type hints don't say so.
    settings = Settings(_env_file=local_settings_file)  # pyright: ignore[reportCallIssue]

    assert settings.usable_ai_key == "made-up-key"


def test_the_ai_key_is_hidden_when_the_settings_are_printed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The key never shows in a log line or an error that prints the settings."""
    monkeypatch.setenv("TAKE5_AI_KEY", "made-up-key")

    assert "made-up-key" not in repr(Settings())


SETTINGS_TEMPLATE: Path = Path(__file__).parents[1] / ".env.example"


def test_the_settings_template_names_every_setting() -> None:
    """`backend/.env.example` shows each setting, so a new one is not missed there."""
    template: str = SETTINGS_TEMPLATE.read_text(encoding="utf-8")

    for field_name in Settings.model_fields:
        assert f"TAKE5_{field_name.upper()}=" in template


def test_the_settings_template_holds_no_key() -> None:
    """The template is in the repo, so its key line must stay empty."""
    template: str = SETTINGS_TEMPLATE.read_text(encoding="utf-8")

    assert "TAKE5_AI_KEY=\n" in template
