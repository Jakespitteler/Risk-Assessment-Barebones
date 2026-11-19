"""Tests for `setup.py`, which sets up a freshly cloned repo from scratch."""

import subprocess
from pathlib import PurePath, PurePosixPath, PureWindowsPath
from unittest.mock import MagicMock, call, patch

import pytest
import setup


@pytest.mark.parametrize(
    ("folder", "service_name"),
    [
        (PureWindowsPath(r"C:\Users\example\OneDrive\GitHub\repo"), "OneDrive"),
        (
            PureWindowsPath(r"C:\Users\example\OneDrive - Example Company\repo"),
            "OneDrive",
        ),
        (PureWindowsPath(r"C:\Users\example\Dropbox (Personal)\repo"), "Dropbox"),
        (PureWindowsPath(r"G:\My Drive\repo"), "Google Drive"),
        (PureWindowsPath(r"C:\Users\example\iCloudDrive\repo"), "iCloud Drive"),
        (
            PurePosixPath("/Users/example/Library/CloudStorage/OneDrive-Personal/repo"),
            "OneDrive",
        ),
        (
            PurePosixPath("/Users/example/Library/CloudStorage/GoogleDrive-a@b.c/repo"),
            "Google Drive",
        ),
        (
            PurePosixPath("/Users/example/Library/Mobile Documents/iCloud"),
            "iCloud Drive",
        ),
    ],
)
def test_repo_in_a_synced_folder_names_the_service(
    folder: PurePath,
    service_name: str,
) -> None:
    """A repo inside a OneDrive, Dropbox, Google Drive or iCloud folder is spotted."""
    assert setup.cloud_sync_service(folder) == service_name


@pytest.mark.parametrize(
    "folder",
    [
        PureWindowsPath(r"C:\Users\example\Documents\GitHub\Risk-Assessment-Barebones"),
        PureWindowsPath(r"C:\dev\Risk-Assessment-Barebones"),
        PurePosixPath("/home/example/dev/Risk-Assessment-Barebones"),
    ],
)
def test_repo_in_a_plain_folder_has_no_service(folder: PurePath) -> None:
    """An ordinary folder gives no warning."""
    assert setup.cloud_sync_service(folder) is None


@pytest.mark.parametrize(
    ("version_text", "version_numbers"),
    [
        ("v22.11.0\n", (22, 11, 0)),
        ("v24.15.1", (24, 15, 1)),
        ("not a version", None),
    ],
)
def test_node_version_numbers_reads_what_node_prints(
    version_text: str,
    version_numbers: tuple[int, ...] | None,
) -> None:
    """The numbers are read from `node --version`, and nonsense gives None."""
    assert setup.node_version_numbers(version_text) == version_numbers


@pytest.mark.parametrize("node_version", ["v22.22.2", "v22.23.4", "v24.15.0"])
def test_ready_node_has_no_problem(node_version: str) -> None:
    """Node.js 22.22.2 or newer, with npm, needs nothing done."""
    assert setup.node_problem(node_version, npm_found=True) is None


@pytest.mark.parametrize(
    ("node_version", "npm_found", "expected_start"),
    [
        (None, True, "Node.js is not installed."),
        ("v20.11.1", True, "Node.js v20.11.1 is too old."),
        ("v22.11.0", True, "Node.js v22.11.0 is too old."),
        ("v22.22.2", False, "npm, which comes with Node.js, is missing."),
    ],
)
def test_node_problem_says_what_is_wrong_and_how_to_install(
    node_version: str | None,
    npm_found: bool,
    expected_start: str,
) -> None:
    """Missing, old or incomplete Node.js is named, with how to install it."""
    problem: str | None = setup.node_problem(node_version, npm_found=npm_found)

    assert problem is not None
    assert problem.startswith(expected_start)
    assert setup.NODE_INSTALL_HELP in problem


def test_missing_git_and_node_are_both_reported() -> None:
    """Every missing tool is listed at once, so one round of installs fixes them all."""
    with (
        patch.object(setup.shutil, "which", return_value=None),
        patch.object(setup, "installed_node_version", return_value=None),
    ):
        problems: list[str] = setup.missing_tools()

    assert problems[0] == setup.GIT_INSTALL_HELP
    assert problems[1].startswith("Node.js is not installed.")
    assert len(problems) == 2


def test_missing_tool_stops_before_installing_anything() -> None:
    """Nothing is installed while a tool is missing."""
    with (
        patch.object(setup, "missing_tools", return_value=[setup.GIT_INSTALL_HELP]),
        patch.object(setup.subprocess, "run") as run,
    ):
        exit_code: int = setup.set_up()

    assert exit_code == 1
    run.assert_not_called()


def test_installs_run_in_order_from_their_folders() -> None:
    """The back end, then the front end, then the test browser, each in its folder."""
    with (
        patch.object(setup, "missing_tools", return_value=[]),
        patch.object(setup, "remember_frontend_install"),
        patch.object(
            setup.subprocess,
            "run",
            return_value=subprocess.CompletedProcess([], 0),
        ) as run,
    ):
        exit_code: int = setup.set_up()

    assert exit_code == 0
    assert run.mock_calls == [
        call(
            step.command,
            cwd=setup.REPO_ROOT / step.folder,
            env=setup.SETUP_ENVIRONMENT,
            check=False,
        )
        for step in setup.INSTALL_STEPS
    ]
    assert [step.command[1] for step in setup.INSTALL_STEPS] == [
        "sync",
        "ci",
        "playwright",
    ]


def test_failed_install_stops_and_passes_on_its_exit_code() -> None:
    """A failed step stops set-up, so later steps don't run on a broken install."""
    run = MagicMock(return_value=subprocess.CompletedProcess([], 3))
    with (
        patch.object(setup, "missing_tools", return_value=[]),
        patch.object(setup.subprocess, "run", run),
    ):
        exit_code: int = setup.set_up()

    assert exit_code == 3
    run.assert_called_once()


def test_synced_folder_warns_at_start_and_end_and_carries_on(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """In a OneDrive folder set-up still installs, warns twice and lists what it did."""
    with (
        patch.object(setup, "remember_frontend_install"),
        patch.object(setup, "cloud_sync_service", return_value="OneDrive"),
        patch.object(setup, "missing_tools", return_value=[]),
        patch.object(
            setup.subprocess,
            "run",
            return_value=subprocess.CompletedProcess([], 0),
        ),
    ):
        exit_code: int = setup.set_up()

    output: str = capsys.readouterr().out
    assert exit_code == 0
    assert output.count(setup.cloud_sync_warning("OneDrive")) == 2
    assert output.startswith("WARNING")
    for step in setup.INSTALL_STEPS:
        assert f"  - {step.what_it_installs}" in output
    assert "uv run start.py" in output


def test_installs_run_without_the_scripts_own_virtual_environment() -> None:
    """The back end's `.venv` is used, not the throwaway one `uv run` made."""
    assert "VIRTUAL_ENV" not in setup.SETUP_ENVIRONMENT


def test_a_failed_install_says_which_command_to_run_again(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`start.py` shares the install steps, and its own name is in the message."""
    failed_install = MagicMock(return_value=subprocess.CompletedProcess([], 1))
    with patch.object(setup.subprocess, "run", failed_install):
        exit_code: int = setup.install(setup.INSTALL_STEPS[1:2], "uv run start.py")

    output: str = capsys.readouterr().out
    assert exit_code == 1
    assert "FAILED while installing the front end's packages" in output
    assert "run `uv run start.py` again" in output


def test_a_finished_set_up_is_remembered_so_start_installs_nothing_more() -> None:
    """Once every install works, the front end is marked installed for its lock file."""
    with (
        patch.object(setup, "missing_tools", return_value=[]),
        patch.object(setup, "install", return_value=0),
        patch.object(setup, "remember_frontend_install") as remember_frontend,
    ):
        exit_code: int = setup.set_up()

    assert exit_code == 0
    remember_frontend.assert_called_once_with(setup.REPO_ROOT / "frontend")
