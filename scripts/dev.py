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
FRONTEND_COMMAND = [shutil.which("npm") or "npm", "run", "dev"]


def start(command: list[str], folder: str) -> subprocess.Popen[bytes]:
    """Start a server in its own process group, so its children can be stopped too."""
    if sys.platform == "win32":
        return subprocess.Popen(
            command,
            cwd=REPO_ROOT / folder,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )
    return subprocess.Popen(command, cwd=REPO_ROOT / folder, start_new_session=True)


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
