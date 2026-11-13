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

REPO_ROOT = Path(__file__).resolve().parent.parent
NPM = shutil.which("npm") or "npm"
NPX = shutil.which("npx") or "npx"

# `uv run` points VIRTUAL_ENV at this script's own throwaway environment. The back end
# must use its own `.venv`, so the checks are run without it.
CHECK_ENVIRONMENT = {
    name: value for name, value in os.environ.items() if name != "VIRTUAL_ENV"
}


class Check(NamedTuple):
    """One check: what it is called, the command, and the folder it runs in."""

    name: str
    command: list[str]
    folder: str


# The back end's ruff and pyright settings also cover the scripts in this folder.
PYTHON_FOLDERS = [".", "../scripts"]
RUFF = ["uv", "run", "ruff"]
RUFF_SETTINGS = ["--config", "pyproject.toml"]

CHECKS = [
    Check("Markdown", [NPX, "--yes", "markdownlint-cli2@0.24.0", "**/*.md"], "."),
    Check(
        "Back end lint", [*RUFF, "check", *RUFF_SETTINGS, *PYTHON_FOLDERS], "backend"
    ),
    Check(
        "Back end format",
        [*RUFF, "format", "--check", *RUFF_SETTINGS, *PYTHON_FOLDERS],
        "backend",
    ),
    Check("Back end types", ["uv", "run", "pyright", *PYTHON_FOLDERS], "backend"),
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
        result = subprocess.run(
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
