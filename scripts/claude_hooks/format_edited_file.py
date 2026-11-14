# /// script
# requires-python = ">=3.13"
# ///
"""Format a file straight after Claude Code edits it, as the checks would want it.

Claude Code runs this after every Edit or Write (a `PostToolUse` hook, set in
`.claude/settings.json`) and passes the call as JSON on standard input. Python goes
through Ruff's formatter, front-end files through Prettier, and Markdown through
markdownlint's safe fixes. It only formats. The one lint fix it applies to Python is
Ruff's trailing comma (`COM812`), which puts one item per line when a line is too long.
It never runs Ruff's other fixes, which would delete an import that Claude added one
edit before using it.

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


def python_format_commands(
    edited_file: Path,
    backend_folder: Path,
) -> tuple[FormatCommand, ...]:
    """Format a Python file so each long signature, call or list has one item per line.

    The formatter runs first, so a short `def` broken over lines by hand goes back onto
    one line. Ruff's trailing comma fix then marks what is still too long, and the
    formatter runs again to put each of those items on its own line.

    Args:
        edited_file: The Python file Claude edited, as an absolute path.
        backend_folder: The back end's folder, which holds the Ruff settings.

    Returns:
        The three commands, in the order they must run.
    """
    ruff_settings: list[str] = ["uv", "run", "ruff", "--config", "pyproject.toml"]
    ruff_format: list[str] = [*ruff_settings, "format", str(edited_file)]
    add_trailing_commas: list[str] = [
        *ruff_settings,
        "check",
        "--fix",
        "--select",
        "COM812",
        str(edited_file),
    ]
    return (
        FormatCommand(ruff_format, backend_folder),
        FormatCommand(add_trailing_commas, backend_folder),
        FormatCommand(ruff_format, backend_folder),
    )


def format_commands_for(
    edited_file: Path,
    repo_root: Path,
) -> tuple[FormatCommand, ...]:
    """Choose the formatters for a file, with the settings `scripts/check.py` uses.

    Args:
        edited_file: The file Claude edited, as an absolute path.
        repo_root: The repository's root folder.

    Returns:
        The formatters to run in order, or none when the file is outside the repo or
        has no formatter.
    """
    if not edited_file.is_relative_to(repo_root):
        return ()
    top_folder: str = edited_file.relative_to(repo_root).parts[0]
    file_type: str = edited_file.suffix
    if file_type == ".py" and top_folder in ("backend", "scripts"):
        return python_format_commands(edited_file, repo_root / "backend")
    if file_type in FRONTEND_SUFFIXES and top_folder == "frontend":
        return (
            FormatCommand(
                [NPX, "--no-install", "prettier", "--write", str(edited_file)],
                repo_root / "frontend",
            ),
        )
    if file_type == ".md":
        literal_path: str = f":{edited_file}"  # `:` stops brackets being read as a glob
        return (
            FormatCommand(
                [NPX, "--yes", MARKDOWNLINT, "--fix", literal_path],
                repo_root,
            ),
        )
    return ()


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


def run_formatter(format_command: FormatCommand) -> subprocess.CompletedProcess[str]:
    """Run one formatter and capture what it prints.

    Args:
        format_command: The formatter to run.

    Returns:
        The finished process, with its exit code and output.
    """
    return subprocess.run(
        format_command.command,
        cwd=format_command.folder,
        env=FORMAT_ENVIRONMENT,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def main() -> int:
    """Read the edit from standard input and format the edited file.

    Returns:
        2 when a formatter failed, so Claude sees why, otherwise 0.
    """
    edited_file: Path | None = edited_file_in(json.load(sys.stdin.buffer))  # UTF-8
    format_commands: tuple[FormatCommand, ...] = (
        format_commands_for(edited_file, REPO_ROOT) if edited_file else ()
    )
    for format_command in format_commands:
        result: subprocess.CompletedProcess[str] = run_formatter(format_command)
        if result.returncode != 0:
            print(result.stdout + result.stderr, file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
