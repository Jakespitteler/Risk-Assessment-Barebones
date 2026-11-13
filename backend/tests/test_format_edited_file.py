"""Tests for the hook that formats each file Claude Code edits."""

from pathlib import Path

import pytest
from scripts.claude_hooks.format_edited_file import (
    NPX,
    FormatCommand,
    format_command_for,
)

REPO_ROOT: Path = Path("/repo")


def test_python_is_formatted_by_ruff_with_the_back_end_settings() -> None:
    """Python in the back end or scripts uses the same Ruff settings as the checks."""
    edited_file: Path = REPO_ROOT / "scripts" / "dev.py"

    assert format_command_for(edited_file, REPO_ROOT) == FormatCommand(
        ["uv", "run", "ruff", "format", "--config", "pyproject.toml", str(edited_file)],
        REPO_ROOT / "backend",
    )


@pytest.mark.parametrize("file_name", ["App.tsx", "client.ts", "index.css"])
def test_front_end_files_are_formatted_by_prettier(file_name: str) -> None:
    """Front-end code is formatted by Prettier, run in the front end's folder."""
    edited_file: Path = REPO_ROOT / "frontend" / "src" / file_name

    assert format_command_for(edited_file, REPO_ROOT) == FormatCommand(
        [NPX, "prettier", "--write", str(edited_file)], REPO_ROOT / "frontend"
    )


def test_markdown_gets_markdownlint_fixes() -> None:
    """Markdown anywhere in the repo gets markdownlint's safe fixes."""
    edited_file: Path = REPO_ROOT / "docs" / "spec.md"
    format_command: FormatCommand | None = format_command_for(edited_file, REPO_ROOT)

    assert format_command is not None
    assert format_command.command[-2:] == ["--fix", str(edited_file)]
    assert format_command.folder == REPO_ROOT


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
    assert format_command_for(edited_file, REPO_ROOT) is None
