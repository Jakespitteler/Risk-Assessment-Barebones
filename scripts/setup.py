# /// script
# requires-python = ">=3.13"
# ///
"""Set up a freshly cloned copy of the repo, so the app and every check can run.

Usage, from the repo root: `uv run scripts/setup.py`. It is safe to run again, for
example after pulling changes that add packages.

First it checks for the tools uv can't install: git and Node.js 22.22.2 or newer. If
one is missing it says how to get it and stops before installing anything. Then it
installs Python 3.13 and the back end's packages, the front end's packages, and the
browser the whole-app tests use. It ends with what it did and what to do next.
"""

import os
import shutil
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path, PurePath
from typing import NamedTuple

REPO_ROOT: Path = Path(__file__).resolve().parent.parent
# The oldest Node.js the locked front-end packages accept (jsdom asks for 22.22.2).
# npm also refuses any package whose stated Node.js range the version misses.
MINIMUM_NODE_VERSION: tuple[int, int, int] = (22, 22, 2)
MINIMUM_NODE_VERSION_TEXT: str = ".".join(
    str(number) for number in MINIMUM_NODE_VERSION
)
# On Windows npm and npx are `.cmd` files, which `shutil.which` finds and a bare name
# would not.
NPM: str = shutil.which("npm") or "npm"
NPX: str = shutil.which("npx") or "npx"

# `uv run` points VIRTUAL_ENV at this script's own throwaway environment. The back end
# must use its own `.venv`, so the installs are run without it.
SETUP_ENVIRONMENT: dict[str, str] = {
    name: value for name, value in os.environ.items() if name != "VIRTUAL_ENV"
}

# cspell:ignore onedrive googledrive iclouddrive
# The start of a folder name each sync service uses, in lower case, and the service's
# name. The macOS folders under ~/Library/CloudStorage start the same way, for example
# "OneDrive-Personal".
CLOUD_SYNC_FOLDER_PREFIXES: dict[str, str] = {
    "onedrive": "OneDrive",
    "dropbox": "Dropbox",
    "google drive": "Google Drive",
    "googledrive": "Google Drive",
    "my drive": "Google Drive",
    "icloud drive": "iCloud Drive",
    "iclouddrive": "iCloud Drive",
    "mobile documents": "iCloud Drive",
}

GIT_INSTALL_HELP: str = (
    "git is not installed. Get it from https://git-scm.com/downloads "
    "(on Windows: winget install --id Git.Git -e)."
)
NODE_INSTALL_HELP: str = (
    f"Install Node.js {MINIMUM_NODE_VERSION_TEXT} or newer from "
    "https://nodejs.org/en/download (on Windows: winget install --id OpenJS.NodeJS.LTS "
    "-e; on macOS: brew install node)."
)
REOPEN_TERMINAL_HELP: str = (
    "After installing, close this terminal, open a new one (so it finds the new tools) "
    "and run `uv run scripts/setup.py` again."
)


class InstallStep(NamedTuple):
    """One thing set-up installs: what it is, the command, and the folder it runs in."""

    what_it_installs: str
    command: list[str]
    folder: str


INSTALL_STEPS: list[InstallStep] = [
    InstallStep(
        "Python 3.13 and the back end's packages",
        ["uv", "sync", "--locked"],
        "backend",
    ),
    InstallStep(
        "the front end's packages",
        [NPM, "ci", "--engine-strict"],
        "frontend",
    ),
    InstallStep(
        "the browser the whole-app tests use",
        [NPX, "playwright", "install", "chromium"],
        "frontend",
    ),
]


def cloud_sync_service(folder: PurePath) -> str | None:
    """Name the sync service whose folder holds this folder, if any.

    Args:
        folder: The folder to look at, such as the repo root.

    Returns:
        "OneDrive", "Dropbox", "Google Drive" or "iCloud Drive", or None when no part
        of the path looks like a sync service's folder.
    """
    for folder_name in folder.parts:
        lower_case_name: str = folder_name.lower()
        for prefix, service_name in CLOUD_SYNC_FOLDER_PREFIXES.items():
            if lower_case_name.startswith(prefix):
                return service_name
    return None


def node_version_numbers(version_text: str) -> tuple[int, ...] | None:
    """Read the numbers from what `node --version` prints.

    Args:
        version_text: The printed version, such as "v22.11.0".

    Returns:
        The numbers, such as (22, 11, 0), or None when the text is not a version.
    """
    number_texts: list[str] = version_text.strip().removeprefix("v").split(".")
    if not all(number_text.isdigit() for number_text in number_texts):
        return None
    return tuple(int(number_text) for number_text in number_texts)


def installed_node_version() -> str | None:
    """Ask Node.js for its version.

    Returns:
        What `node --version` prints, such as "v22.11.0", or None when Node.js is not
        installed or does not answer.
    """
    node_executable: str | None = shutil.which("node")
    if node_executable is None:
        return None
    result: subprocess.CompletedProcess[str] = subprocess.run(
        [node_executable, "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def node_problem(node_version: str | None, npm_found: bool) -> str | None:
    """Say what is wrong with the Node.js install, if anything.

    Args:
        node_version: What `node --version` printed, or None when Node.js is missing.
        npm_found: Whether npm, which comes with Node.js, was found.

    Returns:
        A sentence saying what is missing and how to install it, or None when Node.js
        and npm are ready.
    """
    if node_version is None:
        return f"Node.js is not installed. {NODE_INSTALL_HELP}"
    version_numbers: tuple[int, ...] | None = node_version_numbers(node_version)
    if version_numbers is None or version_numbers < MINIMUM_NODE_VERSION:
        return f"Node.js {node_version} is too old. {NODE_INSTALL_HELP}"
    if not npm_found:
        return f"npm, which comes with Node.js, is missing. {NODE_INSTALL_HELP}"
    return None


def missing_tools() -> list[str]:
    """Check for the tools set-up needs and uv can't install.

    Returns:
        One sentence for each missing tool, saying how to install it. Empty when all
        are ready.
    """
    problems: list[str] = []
    if shutil.which("git") is None:
        problems.append(GIT_INSTALL_HELP)
    node_version_problem: str | None = node_problem(
        installed_node_version(),
        npm_found=shutil.which("npm") is not None,
    )
    if node_version_problem is not None:
        problems.append(node_version_problem)
    return problems


def cloud_sync_warning(service_name: str) -> str:
    """Explain why the repo should not be in a cloud-synced folder.

    Args:
        service_name: The sync service, such as "OneDrive".
    """
    return (
        f"WARNING: this repo is inside a {service_name} folder. {service_name} will "
        "try to sync the twenty thousand or so files set-up installs, can lock files "
        "while they are being written, and can make conflicting copies. Clone the repo "
        "again into a folder that is not synced, such as C:\\dev on Windows or ~/dev "
        "on macOS and Linux."
    )


def install(steps: Sequence[InstallStep]) -> int:
    """Run each install step in turn, stopping at the first that fails.

    Args:
        steps: The steps to run, in order.

    Returns:
        0 when every step worked, otherwise the exit code of the step that failed.
    """
    for step in steps:
        print(f"\n=== Installing {step.what_it_installs} ===", flush=True)
        result: subprocess.CompletedProcess[bytes] = subprocess.run(
            step.command,
            cwd=REPO_ROOT / step.folder,
            env=SETUP_ENVIRONMENT,
            check=False,
        )
        if result.returncode != 0:
            print(
                f"\nFAILED while installing {step.what_it_installs}. Fix the "
                "problem shown above (if the app is running, stop it first), then "
                "run `uv run scripts/setup.py` again.",
            )
            return result.returncode
    return 0


def print_summary(cloud_service: str | None) -> None:
    """Say what set-up did and what to do next.

    Args:
        cloud_service: The sync service whose folder holds the repo, if any.
    """
    print("\nSet-up is complete. It checked git and Node.js, then installed:")
    for step in INSTALL_STEPS:
        print(f"  - {step.what_it_installs}")
    print("\nNext:")
    print("  - Start the app: uv run scripts/dev.py, then open http://localhost:5173")
    print("  - Run every check, as CI does: uv run scripts/check.py")
    print("  - Using VS Code? Pick the interpreter: docs/dev-setup.md, First time.")
    if sys.platform == "linux":
        print(
            "  - On Linux, if the browser tests say libraries are missing, run "
            "`npx playwright install-deps chromium` in frontend/ (it needs sudo).",
        )
    if cloud_service is not None:
        print(f"\n{cloud_sync_warning(cloud_service)}")


def set_up() -> int:
    """Check the tools, install everything, and report.

    Returns:
        0 when set-up finished, otherwise a non-zero exit code.
    """
    cloud_service: str | None = cloud_sync_service(REPO_ROOT)
    if cloud_service is not None:
        print(cloud_sync_warning(cloud_service), flush=True)
    problems: list[str] = missing_tools()
    if problems:
        print("\nSet-up can't start yet. Nothing was installed.")
        for problem in problems:
            print(f"  - {problem}")
        print(REOPEN_TERMINAL_HELP)
        return 1
    install_exit_code: int = install(INSTALL_STEPS)
    if install_exit_code != 0:
        return install_exit_code
    print_summary(cloud_service)
    return 0


if __name__ == "__main__":
    sys.exit(set_up())
