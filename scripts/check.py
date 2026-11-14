# /// script
# requires-python = ">=3.13"
# ///
"""Run every check that CI runs, in the same order, and stop at the first failure.

Usage, from the repo root: `uv run scripts/check.py`.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

REPO_ROOT: Path = Path(__file__).resolve().parent.parent
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
PYTHON_FOLDERS: list[str] = [".", "../scripts"]
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
        "Back end lint", [*RUFF, "check", *RUFF_SETTINGS, *PYTHON_FOLDERS], "backend"
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


def run_checks() -> int:
    """Run each check in turn.

    Returns:
        0 when every check passes, otherwise the exit code of the check that failed.
    """
    for check in CHECKS:
        print(f"\n=== {check.name} ===", flush=True)
        result: subprocess.CompletedProcess[bytes] = subprocess.run(
            check.command,
            cwd=REPO_ROOT / check.folder,
            env=CHECK_ENVIRONMENT,
            check=False,
        )
        if result.returncode != 0:
            print(f"\nFAILED: {check.name}")
            return result.returncode
    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(run_checks())
