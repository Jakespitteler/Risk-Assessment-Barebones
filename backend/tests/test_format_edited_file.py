"""Tests for the hook that formats each file Claude Code edits."""

import io
import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from scripts.claude_hooks import format_edited_file
from scripts.claude_hooks.format_edited_file import (
    NPX,
    FormatCommand,
    format_commands_for,
)

REPO_ROOT: Path = Path("/repo")


def test_python_is_formatted_then_given_trailing_commas_then_formatted_again() -> None:
    """Python gets Ruff's formatter, its trailing comma fix only, then the formatter.

    All three use the back end's Ruff settings, the same as the checks.
    """
    edited_file: Path = REPO_ROOT / "scripts" / "try_challenge.py"
    ruff_settings: list[str] = ["uv", "run", "ruff", "--config", "pyproject.toml"]
    ruff_format: FormatCommand = FormatCommand(
        [*ruff_settings, "format", str(edited_file)],
        REPO_ROOT / "backend",
    )
    add_trailing_commas: FormatCommand = FormatCommand(
        [*ruff_settings, "check", "--fix", "--select", "COM812", str(edited_file)],
        REPO_ROOT / "backend",
    )

    assert format_commands_for(edited_file, REPO_ROOT) == (
        ruff_format,
        add_trailing_commas,
        ruff_format,
    )


@pytest.mark.parametrize("file_name", ["App.tsx", "client.ts", "index.css"])
def test_front_end_files_are_formatted_by_the_installed_prettier(
    file_name: str,
) -> None:
    """Front-end code uses the front end's own Prettier, never a downloaded one."""
    edited_file: Path = REPO_ROOT / "frontend" / "src" / file_name

    assert format_commands_for(edited_file, REPO_ROOT) == (
        FormatCommand(
            [NPX, "--no-install", "prettier", "--write", str(edited_file)],
            REPO_ROOT / "frontend",
        ),
    )


def test_markdown_gets_markdownlint_fixes_on_that_file_only() -> None:
    """The `:` prefix makes markdownlint read the path as a name, not a pattern."""
    edited_file: Path = REPO_ROOT / "docs" / "notes (draft).md"
    (format_command,) = format_commands_for(edited_file, REPO_ROOT)

    assert format_command.command[-2:] == ["--fix", f":{edited_file}"]
    assert format_command.folder == REPO_ROOT


def test_a_command_in_the_repo_root_is_formatted_like_the_scripts() -> None:
    """`start.py` and the other root commands get the same Ruff steps as `scripts/`."""
    edited_file: Path = REPO_ROOT / "start.py"
    script_steps: tuple[FormatCommand, ...] = format_commands_for(
        REPO_ROOT / "scripts" / "try_challenge.py",
        REPO_ROOT,
    )

    root_steps: tuple[FormatCommand, ...] = format_commands_for(edited_file, REPO_ROOT)

    assert len(root_steps) == len(script_steps) == 3
    assert all(step.folder == REPO_ROOT / "backend" for step in root_steps)
    assert all(step.command[-1] == str(edited_file) for step in root_steps)


@pytest.mark.parametrize(
    "edited_file",
    [
        Path("/elsewhere/notes.md"),
        REPO_ROOT / "backend" / "uv.lock",
        REPO_ROOT / ".claude" / "settings.json",
    ],
)
def test_other_files_are_left_alone(edited_file: Path) -> None:
    """Files outside the repo, or with no formatter, are not touched."""
    assert format_commands_for(edited_file, REPO_ROOT) == ()


def run_formatter(
    monkeypatch: pytest.MonkeyPatch,
    file_path: str,
    formatter_results: list[int],
) -> tuple[int, MagicMock]:
    """Run the hook's `main` for an edit, with the formatters replaced by a stand-in.

    Args:
        monkeypatch: pytest's fixture, to feed the hook its standard input.
        file_path: The file the edit names.
        formatter_results: The exit code each formatter call returns, in order.

    Returns:
        The hook's exit code, and the stand-in, to see how it was called.
    """
    hook_input: dict[str, object] = {
        "tool_name": "Edit",
        "tool_input": {"file_path": file_path, "new_string": "Don’t start yet"},
    }
    stdin_bytes: bytes = json.dumps(hook_input, ensure_ascii=False).encode()
    monkeypatch.setattr("sys.stdin", io.TextIOWrapper(io.BytesIO(stdin_bytes)))
    finished_formatters: list[subprocess.CompletedProcess[str]] = [
        subprocess.CompletedProcess(
            [],
            exit_code,
            stdout="",
            stderr="error: unexpected EOF",
        )
        for exit_code in formatter_results
    ]
    with patch.object(
        format_edited_file.subprocess,
        "run",
        side_effect=finished_formatters,
    ) as formatter:
        return format_edited_file.main(), formatter


def test_a_formatter_error_is_shown_to_claude(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Exit code 2 shows Claude the message, and the later formatters don't run."""
    edited_file: Path = format_edited_file.REPO_ROOT / "scripts" / "try_challenge.py"

    exit_code, formatter = run_formatter(monkeypatch, str(edited_file), [1])

    assert exit_code == 2
    formatter.assert_called_once()
    assert "unexpected EOF" in capsys.readouterr().err


def test_a_failed_trailing_comma_fix_stops_before_the_second_format(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When Ruff's comma fix fails, the hook stops there and reports it."""
    edited_file: Path = format_edited_file.REPO_ROOT / "scripts" / "try_challenge.py"

    exit_code, formatter = run_formatter(monkeypatch, str(edited_file), [0, 1])

    assert exit_code == 2
    assert formatter.call_count == 2


def test_every_python_formatter_runs_when_each_succeeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A Python edit runs all three formatters and reports nothing."""
    edited_file: Path = format_edited_file.REPO_ROOT / "scripts" / "try_challenge.py"

    exit_code, formatter = run_formatter(monkeypatch, str(edited_file), [0, 0, 0])

    assert exit_code == 0
    assert formatter.call_count == 3


def test_a_file_outside_the_repo_is_not_formatted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An edit outside the repo runs no formatter and reports nothing."""
    exit_code, formatter = run_formatter(monkeypatch, "/elsewhere/notes.md", [])

    assert exit_code == 0
    formatter.assert_not_called()
