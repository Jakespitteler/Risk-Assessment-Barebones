# /// script
# requires-python = ">=3.13"
# ///
"""Format a file straight after Claude Code edits it, as the checks would want it.

Claude Code runs this after every Edit or Write (a `PostToolUse` hook, set in
`.claude/settings.json`) and passes the call as JSON on standard input. Python goes
through Ruff's formatter, front-end files through Prettier, and Markdown through
markdownlint's safe fixes. It only formats. It never runs `ruff check --fix`, which
would delete an import that Claude added one edit before using it.

The edit has already happened, so this hook can't block it. When the formatter fails,
for example on a syntax error, the hook exits with code 2 so Claude sees the message.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, NamedTuple

REPO_ROOT: Path = Path(__file__).resolve().parents[2]
NPX: str = shutil.which("npx") or "npx"
MARKDOWNLINT: str = "markdownlint-cli2@0.24.0"
FRONTEND_SUFFIXES: frozenset[str] = frozenset(
    {".ts", ".tsx", ".js", ".jsx", ".css", ".json", ".html"}
)

# `uv run` points VIRTUAL_ENV at this script's own environment. Ruff must run in the
# back end's `.venv`, so the formatters are run without it.
FORMAT_ENVIRONMENT: dict[str, str] = {
    name: value for name, value in os.environ.items() if name != "VIRTUAL_ENV"
}


class FormatCommand(NamedTuple):
    """A formatter to run: the command and the folder it runs in."""

    command: list[str]
    folder: Path


def format_command_for(edited_file: Path, repo_root: Path) -> FormatCommand | None:
    """Choose the formatter for a file, with the settings `scripts/check.py` uses.

    Args:
        edited_file: The file Claude edited, as an absolute path.
        repo_root: The repository's root folder.

    Returns:
        The formatter to run, or None when the file is outside the repo or has none.
    """
    if not edited_file.is_relative_to(repo_root):
        return None
    top_folder: str = edited_file.relative_to(repo_root).parts[0]
    file_type: str = edited_file.suffix
    if file_type == ".py" and top_folder in ("backend", "scripts"):
        ruff_format: list[str] = ["uv", "run", "ruff", "format", "--config"]
        return FormatCommand(
            [*ruff_format, "pyproject.toml", str(edited_file)], repo_root / "backend"
        )
    if file_type in FRONTEND_SUFFIXES and top_folder == "frontend":
        return FormatCommand(
            [NPX, "--no-install", "prettier", "--write", str(edited_file)],
            repo_root / "frontend",
        )
    if file_type == ".md":
        literal_path: str = f":{edited_file}"  # `:` stops brackets being read as a glob
        return FormatCommand(
            [NPX, "--yes", MARKDOWNLINT, "--fix", literal_path], repo_root
        )
    return None


def edited_file_in(hook_input: dict[str, Any]) -> Path | None:
    """Find the edited file in what Claude Code sent.

    Args:
        hook_input: The JSON that Claude Code passed on standard input.

    Returns:
        The edited file as an absolute path, or None when the call names no file.
    """
    tool_input: dict[str, Any] = hook_input.get("tool_input") or {}
    file_path: object = tool_input.get("file_path")
    return Path(file_path).resolve() if isinstance(file_path, str) else None


def main() -> int:
    """Read the edit from standard input and format the edited file.

    Returns:
        2 when the formatter failed, so Claude sees why, otherwise 0.
    """
    edited_file: Path | None = edited_file_in(json.load(sys.stdin.buffer))  # UTF-8
    format_command: FormatCommand | None = (
        format_command_for(edited_file, REPO_ROOT) if edited_file else None
    )
    if format_command is None:
        return 0
    result: subprocess.CompletedProcess[str] = subprocess.run(
        format_command.command,
        cwd=format_command.folder,
        env=FORMAT_ENVIRONMENT,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode == 0:
        return 0
    print(result.stdout + result.stderr, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
