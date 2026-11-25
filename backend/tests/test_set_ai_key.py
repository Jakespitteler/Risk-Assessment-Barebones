"""Tests for `set_ai_key.py`, which saves the AI's key in `backend/.env`.

Every test writes to a file of its own, never the real `backend/.env`.
"""

import importlib.util
from importlib.machinery import ModuleSpec
from pathlib import Path
from types import ModuleType

import pytest

SET_AI_KEY_FILE: Path = Path(__file__).resolve().parents[2] / "set_ai_key.py"


def load_set_ai_key() -> ModuleType:
    """Load `set_ai_key.py` from the repo root.

    Returns:
        The loaded module.
    """
    spec: ModuleSpec | None = importlib.util.spec_from_file_location(
        "set_ai_key",
        SET_AI_KEY_FILE,
    )
    assert spec is not None
    assert spec.loader is not None
    module: ModuleType = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


set_ai_key: ModuleType = load_set_ai_key()


@pytest.fixture
def settings_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the command at a settings file in the test's own folder.

    Args:
        tmp_path: The test's own folder.
        monkeypatch: Swaps the command's settings file for the test's.

    Returns:
        Where the test's settings file goes. It doesn't exist yet.
    """
    test_settings_file: Path = tmp_path / ".env"
    monkeypatch.setattr(set_ai_key, "SETTINGS_FILE", test_settings_file)
    return test_settings_file


def paste(monkeypatch: pytest.MonkeyPatch, typed: str) -> None:
    """Have the hidden prompt read what the test gives, in place of a person.

    Args:
        monkeypatch: Swaps out the prompt.
        typed: What the person pastes.
    """

    def give_typed(_prompt: str) -> str:
        """Act as the person pasting at the prompt.

        Args:
            _prompt: The prompt, unused.

        Returns:
            What the person pasted.
        """
        return typed

    monkeypatch.setattr(set_ai_key.getpass, "getpass", give_typed)


def test_a_new_settings_file_holds_only_the_key(
    settings_file: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With no `backend/.env` yet, the command makes it with the key line."""
    paste(monkeypatch, "  made-up-key  \n")

    assert set_ai_key.main() == 0

    assert settings_file.read_text(encoding="utf-8") == "TAKE5_AI_KEY=made-up-key\n"


def test_the_empty_key_line_from_the_template_is_filled_in(
    settings_file: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A file copied from `.env.example` keeps its comments and other settings."""
    settings_file.write_text(
        "\N{BYTE ORDER MARK}# The key.\nTAKE5_AI_KEY=\n# TAKE5_AI_KEY=old-example\n"
        "TAKE5_AI_PROVIDER=chatgpt\n",
        encoding="utf-8",
    )
    paste(monkeypatch, "made-up-key")

    assert set_ai_key.main() == 0

    assert settings_file.read_text(encoding="utf-8") == (
        "# The key.\nTAKE5_AI_KEY=made-up-key\n# TAKE5_AI_KEY=old-example\n"
        "TAKE5_AI_PROVIDER=chatgpt\n"
    )


def test_a_utf16_file_from_powershell_is_saved_again_as_utf8(
    settings_file: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A file made with PowerShell's `>` keeps its lines and becomes UTF-8."""
    settings_file.write_text("TAKE5_AI_PROVIDER=chatgpt\n", encoding="utf-16")
    paste(monkeypatch, "made-up-key")

    assert set_ai_key.main() == 0

    assert settings_file.read_text(encoding="utf-8") == (
        "TAKE5_AI_PROVIDER=chatgpt\nTAKE5_AI_KEY=made-up-key\n"
    )


def test_an_unreadable_file_is_left_alone(
    settings_file: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A file that isn't UTF-8 or UTF-16 is kept, with a message, not a stack trace."""
    unreadable_bytes: bytes = b"TAKE5_AI_PROVIDER=\xff\xfe\xfa\n"
    settings_file.write_bytes(unreadable_bytes)
    paste(monkeypatch, "made-up-key")

    assert set_ai_key.main() == 1

    assert settings_file.read_bytes() == unreadable_bytes
    assert "nothing was saved" in capsys.readouterr().out


@pytest.mark.parametrize(
    "pasted",
    ["made-up key", "\x16", "made-up-key\x16", "made-up\tkey"],
)
def test_a_paste_with_a_space_or_hidden_character_is_not_saved(
    pasted: str,
    settings_file: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A Ctrl+V the terminal didn't paste, or two words, never becomes the key."""
    paste(monkeypatch, pasted)

    assert set_ai_key.main() == 1

    assert not settings_file.exists()
    assert "nothing was saved" in capsys.readouterr().out


def test_an_old_key_is_replaced_and_a_repeated_line_dropped() -> None:
    """Only one key line is left, where the first one was."""
    lines: list[str] = [
        "TAKE5_AI_KEY = old-key",
        "TAKE5_AI_MODEL=claude-sonnet-5-5",
        "TAKE5_AI_KEY=older-key",
    ]

    assert set_ai_key.with_key(lines, "new-key") == [
        "TAKE5_AI_KEY=new-key",
        "TAKE5_AI_MODEL=claude-sonnet-5-5",
    ]


def test_nothing_is_saved_when_no_key_is_pasted(
    settings_file: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Pressing Enter alone leaves the settings as they were."""
    paste(monkeypatch, "   ")

    assert set_ai_key.main() == 1

    assert not settings_file.exists()
    assert "nothing was saved" in capsys.readouterr().out


def test_ctrl_c_saves_nothing(
    settings_file: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Stopping at the prompt ends quietly, with no stack trace and no file."""

    def stop(_prompt: str) -> str:
        """Act as a person pressing Ctrl+C at the prompt.

        Args:
            _prompt: The prompt, unused.

        Raises:
            KeyboardInterrupt: Always.
        """
        raise KeyboardInterrupt

    monkeypatch.setattr(set_ai_key.getpass, "getpass", stop)

    assert set_ai_key.main() == 1

    assert not settings_file.exists()


def test_the_key_is_never_printed(
    settings_file: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The key goes in the file and nowhere on the screen."""
    paste(monkeypatch, "made-up-key")

    set_ai_key.main()

    printed_out, printed_err = capsys.readouterr()
    assert "made-up-key" not in printed_out + printed_err
    assert "made-up-key" in settings_file.read_text(encoding="utf-8")
