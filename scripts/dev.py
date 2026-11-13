# /// script
# requires-python = ">=3.13"
# ///
"""Start the back end and the front end together, for working on the app.

Usage, from the repo root: `uv run scripts/dev.py`, then open http://localhost:5173.
Both restart by themselves when their code changes. Press Ctrl+C to stop both.
"""

import shutil
import subprocess
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


def run_both() -> None:
    """Run both servers until either one stops or Ctrl+C is pressed, then stop both."""
    servers = [
        subprocess.Popen(BACKEND_COMMAND, cwd=REPO_ROOT / "backend"),
        subprocess.Popen(FRONTEND_COMMAND, cwd=REPO_ROOT / "frontend"),
    ]
    try:
        while all(server.poll() is None for server in servers):
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        for server in servers:
            server.terminate()
            server.wait()


if __name__ == "__main__":
    run_both()
