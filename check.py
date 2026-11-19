# /// script
# requires-python = ">=3.13"
# ///
"""Run every check that CI runs, in the same order, and stop at the first failure.

Usage, from the repo root: `uv run check.py`. With `--fix` it changes the code instead
of checking it: it formats everything, makes the fixes the lint tools can make by
themselves, and writes the API types again. Run `uv run check.py` afterwards to see what
is left.
"""

import os
import shutil
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import NamedTuple

REPO_ROOT: Path = Path(__file__).resolve().parent
NPM: str = shutil.which("npm") or "npm"
NPX: str = shutil.which("npx") or "npx"

# `uv run` points VIRTUAL_ENV at this script's own throwaway environment. The back end
# must use its own `.venv`, so the checks are run without it.
CHECK_ENVIRONMENT: dict[str, str] = {
    name: value for name, value in os.environ.items() if name != "VIRTUAL_ENV"
}


class Check(NamedTuple):
    """One check: what it is called, the command, and the folder it runs in."""

    name: str
    command: list[str]
    folder: str


# Ruff uses the back end's settings; Pyright uses the root pyproject.toml. The lint runs
# before the format check, so a missing trailing comma (COM812) is named as the cause.
# The paths are from `backend/`, where both run: the back end, the scripts, and the
# commands in the repo root.
PYTHON_FOLDERS: list[str] = [
    ".",
    "../scripts",
    "../start.py",
    "../setup.py",
    "../check.py",
    "../test.py",
]
RUFF: list[str] = ["uv", "run", "ruff"]
RUFF_SETTINGS: list[str] = ["--config", "pyproject.toml"]
# cspell with the Australian English dictionary that Jake's VS Code spell checker uses.
SPELL_CHECKER: list[str] = [
    "-p",
    "cspell@10.5.0",
    "-p",
    "@cspell/dict-en-au@1.1.31",
    "cspell",
    "--config",
    ".cspell/cli.json",
    "--no-progress",
]

CHECKS: list[Check] = [
    Check("Markdown", [NPX, "--yes", "markdownlint-cli2@0.24.0", "**/*.md"], "."),
    Check("Spelling", [NPX, "--yes", *SPELL_CHECKER, "**"], "."),
    Check(
        "Back end lint",
        [*RUFF, "check", *RUFF_SETTINGS, *PYTHON_FOLDERS],
        "backend",
    ),
    Check(
        "Back end format",
        [*RUFF, "format", "--check", *RUFF_SETTINGS, *PYTHON_FOLDERS],
        "backend",
    ),
    Check(
        "Back end types",
        ["uv", "run", "pyright", "--project", "..", *PYTHON_FOLDERS],
        "backend",
    ),
    Check("Back end tests", ["uv", "run", "pytest"], "backend"),
    Check("Front end lint", [NPM, "run", "lint"], "frontend"),
    Check("Front end format", [NPM, "run", "format:check"], "frontend"),
    Check("Front end types", [NPM, "run", "typecheck"], "frontend"),
    Check("Front end tests", [NPM, "test"], "frontend"),
    Check("Regenerate the API types", [NPM, "run", "generate:api"], "frontend"),
    Check(
        "API types match the back end",
        ["git", "diff", "--exit-code", "src/api"],
        "frontend",
    ),
    Check("Whole app in a browser", [NPM, "run", "test:e2e"], "frontend"),
]


FIXES: list[Check] = [
    Check(
        "Back end lint fixes",
        [*RUFF, "check", "--fix", *RUFF_SETTINGS, *PYTHON_FOLDERS],
        "backend",
    ),
    Check(
        "Back end format",
        [*RUFF, "format", *RUFF_SETTINGS, *PYTHON_FOLDERS],
        "backend",
    ),
    Check("Front end lint fixes", [NPM, "run", "lint", "--", "--fix"], "frontend"),
    Check("Front end format", [NPM, "run", "format"], "frontend"),
    Check(
        "Markdown fixes",
        [NPX, "--yes", "markdownlint-cli2@0.24.0", "--fix", "**/*.md"],
        ".",
    ),
    Check("Regenerate the API types", [NPM, "run", "generate:api"], "frontend"),
]


def run_command(check: Check) -> int:
    """Run one check or fix in its folder, under a heading.

    Args:
        check: The check or fix to run.

    Returns:
        Its exit code.
    """
    print(f"\n=== {check.name} ===", flush=True)
    result: subprocess.CompletedProcess[bytes] = subprocess.run(
        check.command,
        cwd=REPO_ROOT / check.folder,
        env=CHECK_ENVIRONMENT,
        check=False,
    )
    return result.returncode


def run_checks(checks: Sequence[Check] = CHECKS) -> int:
    """Run each check in turn, stopping at the first failure, as CI does.

    Args:
        checks: The checks to run, in order.

    Returns:
        0 when every check passes, otherwise the exit code of the check that failed.
    """
    for check in checks:
        exit_code: int = run_command(check)
        if exit_code != 0:
            print(f"\nFAILED: {check.name}")
            return exit_code
    print("\nAll checks passed.")
    return 0


def run_fixes(fixes: Sequence[Check] = FIXES) -> int:
    """Run every fix, even after one reports a problem it couldn't fix.

    A lint fix that leaves one problem behind still fixed the rest, and the formatters
    after it still have work to do.

    Args:
        fixes: The fixes to run, in order.

    Returns:
        0 when nothing is left to fix, otherwise the first non-zero exit code.
    """
    left_to_fix: list[str] = []
    first_exit_code: int = 0
    for fix in fixes:
        exit_code: int = run_command(fix)
        if exit_code != 0:
            left_to_fix.append(fix.name)
            first_exit_code = first_exit_code or exit_code
    if left_to_fix:
        print(
            f"\nFixes done, but these found problems they can't fix: "
            f"{', '.join(left_to_fix)}. See above.",
        )
    else:
        print("\nFixes done. Run `uv run check.py` to see that everything passes.")
    return first_exit_code


def main(arguments: Sequence[str]) -> int:
    """Check everything, or fix what can be fixed with `--fix`.

    Args:
        arguments: What followed the script's name on the command line.

    Returns:
        The exit code: 0 when everything passed or was fixed, 2 for an unknown
        argument, otherwise the exit code of the check or fix that failed.
    """
    if not arguments:
        return run_checks(CHECKS)
    if list(arguments) == ["--fix"]:
        return run_fixes(FIXES)
    print("Usage: uv run check.py [--fix]")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
