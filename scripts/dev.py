# /// script
# requires-python = ">=3.13"
# ///
"""Start the back end and the front end together, for working on the app.

Usage, from the repo root: `uv run scripts/dev.py`, then open the address it prints
last, http://localhost:5173. Both restart by themselves when their code changes. Press
Ctrl+C to stop both.
"""

import os
import shutil
import signal
import subprocess
import sys
import time
from http.client import HTTPResponse
from pathlib import Path
from urllib.request import urlopen

REPO_ROOT: Path = Path(__file__).resolve().parent.parent

BACKEND_COMMAND: list[str] = [
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
NPM: str = shutil.which("npm") or "npm"
FRONTEND_COMMAND: list[str] = [NPM, "run", "dev"]
BACKEND_READY_URL: str = "http://127.0.0.1:8000/api/take5/template"
# The app itself, served by Vite. Uvicorn also prints its own address (port 8000), which
# is only the API, so this one is printed last, once the app answers.
APP_URL: str = "http://localhost:5173"
READY_MESSAGE: str = f"\nThe Take 5 app is ready. Open {APP_URL}  (Ctrl+C stops it.)\n"

# `uv run` points VIRTUAL_ENV at this script's own throwaway environment. The back end
# must use its own `.venv`, so the servers are started without it.
SERVER_ENVIRONMENT: dict[str, str] = {
    name: value for name, value in os.environ.items() if name != "VIRTUAL_ENV"
}


def install_frontend_if_needed() -> None:
    """Install packages when Vite is missing, including after an interrupted install."""
    node_modules: Path = REPO_ROOT / "frontend" / "node_modules"
    vite_executable: str = "vite.cmd" if sys.platform == "win32" else "vite"
    if not (
        (node_modules / ".bin" / vite_executable).is_file()
        and (node_modules / "vite" / "bin" / "vite.js").is_file()
    ):
        subprocess.run(
            [NPM, "ci"],
            cwd=REPO_ROOT / "frontend",
            env=SERVER_ENVIRONMENT,
            check=True,
        )


def wait_until_ready(
    server: subprocess.Popen[bytes],
    url: str,
    name: str,
    timeout: float = 30.0,
) -> None:
    """Wait for a server to answer, failing if its process exits or time runs out.

    Args:
        server: The server's process.
        url: An address that answers 200 once the server is ready.
        name: What the server is called in an error, such as "back end".
        timeout: Seconds to wait before giving up.

    Raises:
        RuntimeError: The server stopped first.
        TimeoutError: The server didn't answer in time.
    """
    deadline: float = time.monotonic() + timeout
    response: HTTPResponse
    while time.monotonic() < deadline:
        if server.poll() is not None:
            raise RuntimeError(f"The {name} stopped before it was ready.")
        try:
            with urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except OSError:
            pass
        time.sleep(0.1)
    raise TimeoutError(f"The {name} did not become ready. Check its output above.")


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
        command,
        cwd=REPO_ROOT / folder,
        env=SERVER_ENVIRONMENT,
        start_new_session=True,
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
    subprocess.run(
        ["uv", "sync", "--locked"],
        cwd=REPO_ROOT / "backend",
        env=SERVER_ENVIRONMENT,
        check=True,
    )
    install_frontend_if_needed()
    servers: list[subprocess.Popen[bytes]] = []
    try:
        backend: subprocess.Popen[bytes] = start(BACKEND_COMMAND, "backend")
        servers.append(backend)
        wait_until_ready(backend, BACKEND_READY_URL, "back end")
        frontend: subprocess.Popen[bytes] = start(FRONTEND_COMMAND, "frontend")
        servers.append(frontend)
        wait_until_ready(frontend, APP_URL, "front end")
        print(READY_MESSAGE, flush=True)
        while all(server.poll() is None for server in servers):
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        for server in servers:
            stop(server)


if __name__ == "__main__":
    run_both()
