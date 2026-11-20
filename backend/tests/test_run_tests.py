"""Tests for `test.py`, which runs the tests from the repo root.

It is loaded from its file: `import test` would find Python's own `test` package.
"""

import importlib.util
import subprocess
from importlib.machinery import ModuleSpec
from pathlib import Path
from types import ModuleType
from unittest.mock import call, patch

import pytest

TEST_COMMAND_FILE: Path = Path(__file__).resolve().parents[2] / "test.py"


def load_test_command() -> ModuleType:
    """Load `test.py` from the repo root under a name of its own.

    Returns:
        The loaded module.
    """
    spec: ModuleSpec | None = importlib.util.spec_from_file_location(
        "test_command",
        TEST_COMMAND_FILE,
    )
    assert spec is not None
    assert spec.loader is not None
    module: ModuleType = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


test_command: ModuleType = load_test_command()


def commands_run_for(arguments: list[str]) -> tuple[int, list[tuple[list[str], Path]]]:
    """Run `test.py` with the arguments, every test tool succeeding.

    Args:
        arguments: What follows `uv run test.py`.

    Returns:
        The exit code, and each command started with the folder it ran in.
    """
    with patch.object(
        test_command.subprocess,
        "run",
        return_value=subprocess.CompletedProcess([], 0),
    ) as run:
        exit_code: int = test_command.main(arguments)
    return exit_code, [(each.args[0], each.kwargs["cwd"]) for each in run.mock_calls]


def test_with_nothing_after_it_all_three_kinds_run_in_order() -> None:
    """Pytest in backend/, then Vitest, then Playwright in frontend/."""
    npm: str = test_command.NPM
    repo_root: Path = test_command.REPO_ROOT

    exit_code, commands = commands_run_for([])

    assert exit_code == 0
    assert commands == [
        (["uv", "run", "pytest"], repo_root / "backend"),
        ([npm, "test", "--"], repo_root / "frontend"),
        ([npm, "run", "test:e2e", "--"], repo_root / "frontend"),
    ]


@pytest.mark.parametrize(
    ("arguments", "expected_command"),
    [
        (["backend"], ["uv", "run", "pytest"]),
        (["backend", "-m", "real_ai"], ["uv", "run", "pytest", "-m", "real_ai"]),
        (["frontend", "StepBar"], ["npm", "test", "--", "StepBar"]),
        (["e2e", "drafts.spec.ts"], ["npm", "run", "test:e2e", "--", "drafts.spec.ts"]),
    ],
)
def test_one_kind_runs_alone_with_the_rest_passed_to_its_tool(
    arguments: list[str],
    expected_command: list[str],
) -> None:
    """`uv run test.py backend -m real_ai` reaches pytest as `pytest -m real_ai`."""
    exit_code, commands = commands_run_for(arguments)

    ((command, _folder),) = commands
    assert exit_code == 0
    assert [Path(command[0]).stem, *command[1:]] == expected_command


def test_the_tests_run_in_the_back_ends_own_environment() -> None:
    """`uv run` makes a throwaway VIRTUAL_ENV for the script; pytest must not use it."""
    with patch.object(
        test_command.subprocess,
        "run",
        return_value=subprocess.CompletedProcess([], 0),
    ) as run:
        test_command.main(["backend"])

    assert run.mock_calls == [
        call(
            ["uv", "run", "pytest"],
            cwd=test_command.REPO_ROOT / "backend",
            env=test_command.TEST_ENVIRONMENT,
            check=False,
        ),
    ]
    assert "VIRTUAL_ENV" not in test_command.TEST_ENVIRONMENT


def test_a_failure_stops_the_later_kinds_and_passes_on_its_exit_code(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """When the back-end tests fail, the slower browser tests don't start."""
    with patch.object(
        test_command.subprocess,
        "run",
        return_value=subprocess.CompletedProcess([], 1),
    ) as run:
        exit_code: int = test_command.main([])

    assert exit_code == 1
    run.assert_called_once()
    assert "FAILED: Back end tests" in capsys.readouterr().out


def test_an_unknown_kind_runs_nothing_and_shows_how_to_use_it(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A typo, or tool arguments with no kind, is not guessed at."""
    exit_code, commands = commands_run_for(["-m", "real_ai"])

    assert exit_code == 2
    assert commands == []
    assert "uv run test.py [backend|frontend|e2e]" in capsys.readouterr().out
