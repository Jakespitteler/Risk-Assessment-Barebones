# /// script
# requires-python = ">=3.13"
# ///
"""Start the back end and the front end together, for working on the app.

Usage, from the repo root: `uv run scripts/dev.py`, then open http://localhost:5173.
Both restart by themselves when their code changes. Press Ctrl+C to stop both.
"""

import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

BACKEND_COMMAND = [
    "uv",
    "run",
    "uvicorn",
    "risk_assessment.api.app:create_app",
    "--factory",
    "--reload",
    "--port",
    "8000",
]
# On Windows npm is `npm.cmd`, which `shutil.which` finds and a bare "npm" would not.
NPM = shutil.which("npm") or "npm"
FRONTEND_COMMAND = [NPM, "run", "dev"]

# `uv run` points VIRTUAL_ENV at this script's own throwaway environment. The back end
# must use its own `.venv`, so the servers are started without it.
SERVER_ENVIRONMENT = {
    name: value for name, value in os.environ.items() if name != "VIRTUAL_ENV"
}


def install_frontend_if_needed() -> None:
    """Install the front end's packages the first time, so one command is enough."""
    if not (REPO_ROOT / "frontend" / "node_modules").exists():
        subprocess.run(
            [NPM, "ci"], cwd=REPO_ROOT / "frontend", env=SERVER_ENVIRONMENT, check=True
        )


def start(command: list[str], folder: str) -> subprocess.Popen[bytes]:
    """Start a server in its own process group, so its children can be stopped too."""
    if sys.platform == "win32":
        return subprocess.Popen(
            command,
            cwd=REPO_ROOT / folder,
            env=SERVER_ENVIRONMENT,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )
    return subprocess.Popen(
        command, cwd=REPO_ROOT / folder, env=SERVER_ENVIRONMENT, start_new_session=True
    )


def stop(server: subprocess.Popen[bytes]) -> None:
    """Stop a server and every process it started (npm and uv each start another)."""
    if server.poll() is not None:
        return
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(server.pid)],
            capture_output=True,
            check=False,
        )
    else:
        os.killpg(server.pid, signal.SIGTERM)
    server.wait()


def run_both() -> None:
    """Run both servers until either one stops or Ctrl+C is pressed, then stop both."""
    install_frontend_if_needed()
    servers = [start(BACKEND_COMMAND, "backend"), start(FRONTEND_COMMAND, "frontend")]
    try:
        while all(server.poll() is None for server in servers):
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        for server in servers:
            stop(server)


if __name__ == "__main__":
    run_both()
