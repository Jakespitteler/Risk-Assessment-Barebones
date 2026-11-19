"""Tests for `check.py`: every check CI runs, and `--fix` for what can be fixed."""

import subprocess
from unittest.mock import MagicMock, call, patch

import check
import pytest


def run_with_success(arguments: list[str]) -> tuple[int, MagicMock]:
    """Run `check.py` with every command it starts succeeding.

    Args:
        arguments: What follows `uv run check.py`.

    Returns:
        The exit code, and the stand-in for running a command.
    """
    with patch.object(
        check.subprocess,
        "run",
        return_value=subprocess.CompletedProcess([], 0),
    ) as run:
        return check.main(arguments), run


def test_with_nothing_after_it_every_check_runs_in_order() -> None:
    """The same checks as CI, each in its folder."""
    exit_code, run = run_with_success([])

    assert exit_code == 0
    assert run.mock_calls == [
        call(
            each.command,
            cwd=check.REPO_ROOT / each.folder,
            env=check.CHECK_ENVIRONMENT,
            check=False,
        )
        for each in check.CHECKS
    ]


def test_fix_formats_fixes_and_writes_the_api_types_without_checking() -> None:
    """`--fix` runs only the fixes: Ruff, ESLint, Prettier, markdownlint, API types."""
    exit_code, run = run_with_success(["--fix"])

    commands: list[list[str]] = [each.args[0] for each in run.mock_calls]
    assert exit_code == 0
    assert commands == [each.command for each in check.FIXES]
    assert commands[0][3:5] == ["check", "--fix"]
    assert commands[1][3] == "format"
    assert "--check" not in commands[1]
    assert commands[2][1:] == ["run", "lint", "--", "--fix"]
    assert commands[3][1:] == ["run", "format"]
    assert "--fix" in commands[4]
    assert commands[5][1:] == ["run", "generate:api"]


def test_fix_and_check_cover_the_commands_in_the_repo_root() -> None:
    """Ruff and Pyright see start.py, setup.py, check.py and test.py too."""
    for name in ("start.py", "setup.py", "check.py", "test.py"):
        assert f"../{name}" in check.PYTHON_FOLDERS


def test_a_failed_check_stops_the_rest_and_passes_on_its_exit_code(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The first failure is named, and later checks don't run."""
    run = MagicMock(return_value=subprocess.CompletedProcess([], 5))
    with patch.object(check.subprocess, "run", run):
        exit_code: int = check.main([])

    assert exit_code == 5
    run.assert_called_once()
    assert f"FAILED: {check.CHECKS[0].name}" in capsys.readouterr().out


def test_fix_runs_every_fix_even_after_one_leaves_a_problem(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A lint error Ruff can't fix doesn't stop the formatters running."""
    results: list[subprocess.CompletedProcess[bytes]] = [
        subprocess.CompletedProcess([], 1),
        *(subprocess.CompletedProcess([], 0) for _ in check.FIXES[1:]),
    ]
    with patch.object(check.subprocess, "run", side_effect=results) as run:
        exit_code: int = check.main(["--fix"])

    assert exit_code == 1
    assert run.call_count == len(check.FIXES)
    assert check.FIXES[0].name in capsys.readouterr().out


def test_an_unknown_argument_shows_how_to_use_it(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Anything but `--fix`, such as a mistyped switch, runs nothing."""
    exit_code, run = run_with_success(["--repair"])

    assert exit_code == 2
    run.assert_not_called()
    assert "uv run check.py [--fix]" in capsys.readouterr().out
