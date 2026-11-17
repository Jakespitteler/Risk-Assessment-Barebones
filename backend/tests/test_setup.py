"""Tests for the one-line set-up of a freshly cloned repo (`scripts/setup.py`)."""

import subprocess
from pathlib import PurePath, PurePosixPath, PureWindowsPath
from unittest.mock import MagicMock, call, patch

import pytest

from scripts import setup


@pytest.mark.parametrize(
    ("folder", "service_name"),
    [
        (PureWindowsPath(r"C:\Users\jake\OneDrive\GitHub\repo"), "OneDrive"),
        (PureWindowsPath(r"C:\Users\jake\OneDrive - Talison\repo"), "OneDrive"),
        (PureWindowsPath(r"C:\Users\jake\Dropbox (Personal)\repo"), "Dropbox"),
        (PureWindowsPath(r"G:\My Drive\repo"), "Google Drive"),
        (PureWindowsPath(r"C:\Users\jake\iCloudDrive\repo"), "iCloud Drive"),
        (
            PurePosixPath("/Users/jake/Library/CloudStorage/OneDrive-Personal/repo"),
            "OneDrive",
        ),
        (
            PurePosixPath("/Users/jake/Library/CloudStorage/GoogleDrive-a@b.c/repo"),
            "Google Drive",
        ),
        (
            PurePosixPath("/Users/jake/Library/Mobile Documents/com~apple~CloudDocs"),
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
        PureWindowsPath(r"C:\Users\jake\Documents\GitHub\Risk-Assessment-Barebones"),
        PureWindowsPath(r"C:\dev\Risk-Assessment-Barebones"),
        PurePosixPath("/home/jake/dev/Risk-Assessment-Barebones"),
    ],
)
def test_repo_in_a_plain_folder_has_no_service(folder: PurePath) -> None:
    """An ordinary folder gives no warning."""
    assert setup.cloud_sync_service(folder) is None


@pytest.mark.parametrize(
    ("version_text", "major_version"),
    [("v22.11.0\n", 22), ("v24.0.1", 24), ("v8.17.0", 8), ("not a version", None)],
)
def test_node_major_version_reads_what_node_prints(
    version_text: str,
    major_version: int | None,
) -> None:
    """The major version is read from `node --version`, and nonsense gives None."""
    assert setup.node_major_version(version_text) == major_version


def test_ready_node_has_no_problem() -> None:
    """Node.js 22 or newer with npm needs nothing done."""
    assert setup.node_problem("v22.0.0", npm_found=True) is None


@pytest.mark.parametrize(
    ("node_version", "npm_found", "expected_start"),
    [
        (None, True, "Node.js is not installed."),
        ("v20.11.1", True, "Node.js v20.11.1 is too old."),
        ("v22.0.0", False, "npm, which comes with Node.js, is missing."),
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


def test_installs_run_without_the_scripts_own_virtual_environment() -> None:
    """The back end's `.venv` is used, not the throwaway one `uv run` made."""
    assert "VIRTUAL_ENV" not in setup.SETUP_ENVIRONMENT
