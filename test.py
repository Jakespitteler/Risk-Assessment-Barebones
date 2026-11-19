# /// script
# requires-python = ">=3.13"
# ///
"""Run the tests from the repo root, with no need to change folder first.

Usage, from the repo root:

- `uv run test.py` runs every kind in turn (back end, front end, then the whole app in
  a browser) and stops at the first that fails.
- `uv run test.py backend`, `uv run test.py frontend` or `uv run test.py e2e` runs one
  kind. Anything after it goes to that kind's test tool: pytest, Vitest or Playwright.
  For example, `uv run test.py backend -m real_ai` runs the test that calls the real AI,
  and `uv run test.py backend tests/domain` runs only the domain tests.
"""

import os
import shutil
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import NamedTuple

REPO_ROOT: Path = Path(__file__).resolve().parent
# On Windows npm is `npm.cmd`, which `shutil.which` finds and a bare "npm" would not.
NPM: str = shutil.which("npm") or "npm"

# `uv run` points VIRTUAL_ENV at this script's own throwaway environment. The back end
# must use its own `.venv`, so the tests are run without it.
TEST_ENVIRONMENT: dict[str, str] = {
    name: value for name, value in os.environ.items() if name != "VIRTUAL_ENV"
}


class KindOfTest(NamedTuple):
    """One kind of test: what it is called, the command, and the folder it runs in.

    The command ends where the extra arguments go: after `--` for an npm script, so npm
    passes them on to the test tool rather than reading them itself.
    """

    name: str
    command: list[str]
    folder: str


TEST_KINDS: dict[str, KindOfTest] = {
    "backend": KindOfTest("Back end tests", ["uv", "run", "pytest"], "backend"),
    "frontend": KindOfTest("Front end tests", [NPM, "test", "--"], "frontend"),
    "e2e": KindOfTest(
        "Whole app in a browser",
        [NPM, "run", "test:e2e", "--"],
        "frontend",
    ),
}
USAGE: str = (
    "Usage: uv run test.py [backend|frontend|e2e] [anything for that test tool]\n"
    "With no kind named it runs all three, and takes nothing else."
)


def commands_for(arguments: Sequence[str]) -> list[KindOfTest] | None:
    """Choose what to run from the words after `uv run test.py`.

    Args:
        arguments: What followed the script's name on the command line.

    Returns:
        The tests to run, in order, each with any extra arguments added to its
        command. None when the arguments don't name a kind of test.
    """
    if not arguments:
        return list(TEST_KINDS.values())
    kind: KindOfTest | None = TEST_KINDS.get(arguments[0])
    if kind is None:
        return None
    return [kind._replace(command=[*kind.command, *arguments[1:]])]


def run_tests(kinds: Sequence[KindOfTest]) -> int:
    """Run each kind of test in turn, stopping at the first that fails.

    Args:
        kinds: The tests to run, in order.

    Returns:
        0 when every test passed, otherwise the exit code of the kind that failed.
    """
    for kind in kinds:
        print(f"\n=== {kind.name} ===", flush=True)
        result: subprocess.CompletedProcess[bytes] = subprocess.run(
            kind.command,
            cwd=REPO_ROOT / kind.folder,
            env=TEST_ENVIRONMENT,
            check=False,
        )
        if result.returncode != 0:
            print(f"\nFAILED: {kind.name}")
            return result.returncode
    return 0


def main(arguments: Sequence[str]) -> int:
    """Run the tests the arguments ask for.

    Args:
        arguments: What followed the script's name on the command line.

    Returns:
        The exit code: 0 when the tests passed, 2 when the arguments name no kind of
        test, otherwise the exit code of the tests that failed.
    """
    kinds: list[KindOfTest] | None = commands_for(arguments)
    if kinds is None:
        print(USAGE)
        return 2
    return run_tests(kinds)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
