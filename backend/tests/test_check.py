"""Tests for `check.py`: every check CI runs, `--fix`, and `--no-front-end`."""

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


def test_no_front_end_runs_every_other_check_in_order() -> None:
    """Markdown, spelling and the whole back end run; nothing in `frontend/` does."""
    exit_code, run = run_with_success(["--no-front-end"])

    folders_run: set[str] = {str(each.kwargs["cwd"]) for each in run.mock_calls}
    commands_run: list[list[str]] = [each.args[0] for each in run.mock_calls]
    by_name: dict[str, check.Check] = {each.name: each for each in check.CHECKS}
    assert exit_code == 0
    assert folders_run == {
        str(check.REPO_ROOT),
        str(check.REPO_ROOT / "backend"),
    }
    for name in ("Markdown", "Spelling", "Back end types", "Back end tests"):
        assert by_name[name].command in commands_run
    assert commands_run == [
        each.command for each in check.CHECKS if each.folder != "frontend"
    ]


def test_fix_formats_fixes_and_writes_the_api_types_without_checking() -> None:
    """`--fix` runs only the fixes: Ruff, ESLint, Prettier, markdownlint, API types.

    Ruff formats before and after its lint fixes, so a trailing comma (COM812) added
    to a line the formatter wrapped is followed by one item per line.
    """
    exit_code, run = run_with_success(["--fix"])

    commands: list[list[str]] = [each.args[0] for each in run.mock_calls]
    assert exit_code == 0
    assert commands == [each.command for each in check.FIXES]
    assert commands[0][3] == "format"
    assert "--check" not in commands[0]
    assert commands[1][3:5] == ["check", "--fix"]
    assert commands[2] == commands[0]
    assert commands[3][1:] == ["run", "lint", "--", "--fix"]
    assert commands[4][1:] == ["run", "format"]
    assert "--fix" in commands[5]
    assert commands[6][1:] == ["run", "generate:api"]


def test_fix_and_check_cover_the_commands_in_the_repo_root() -> None:
    """Ruff and Pyright see start.py, install.py, check.py and test.py too."""
    for name in ("start.py", "install.py", "check.py", "test.py"):
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
    """Anything but the two switches, such as a mistyped one, runs nothing."""
    exit_code, run = run_with_success(["--repair"])

    assert exit_code == 2
    run.assert_not_called()
    assert "uv run check.py [--fix | --no-front-end]" in capsys.readouterr().out
