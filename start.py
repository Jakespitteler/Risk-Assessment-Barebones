# /// script
# requires-python = ">=3.13"
# ///
"""Set up what isn't set up yet, bring the installs in line, and start the app.

Usage, from the repo root: `uv run start.py`, then open the one address it prints.
Press Ctrl+C to stop it. Both halves restart by themselves when their code changes.

In order, it:

1. Stops if ports 8000 or 5173 are already in use, before installing anything, since the
   app is probably running in another terminal.
2. Checks for git and Node.js, as `install.py` does.
3. Brings the installs in line with the lock files the repo holds: the back end's
   packages every time (quick when nothing changed), and the front end's, then the
   browser the whole-app tests use, only when `package-lock.json` changed since they
   were installed. It installs exactly the locked versions and never upgrades one.
4. Starts the back end, then the front end, and prints the app's address once it
   answers. Their own status lines, including those that give their own addresses,
   are turned off in their settings: uvicorn's start-up, restart and shutdown lines in
   `backend/dev_logging.json`, and Vite's address box with `--logLevel warn`. Requests,
   the app's own lines, reload notices, warnings and errors still show.
5. Restarts the back end itself when a Python file under `backend/src` is saved, rather
   than using uvicorn's `--reload`. On Windows that reloader restarts by sending Ctrl+C,
   which Windows gives to every program in the terminal, so it stopped the whole app. A
   change that breaks the back end prints its error and leaves the front end running,
   and the next save starts the back end again.
"""

import contextlib
import os
import signal
import socket
import subprocess
import sys
import time
from collections.abc import Mapping
from http.client import HTTPResponse
from pathlib import Path
from types import FrameType
from urllib.request import OpenerDirector, ProxyHandler, build_opener

import install

REPO_ROOT: Path = Path(__file__).resolve().parent
BACKEND: Path = REPO_ROOT / "backend"
FRONTEND: Path = REPO_ROOT / "frontend"
START_COMMAND: str = "uv run start.py"

API_PORT: int = 8000
APP_PORT: int = 5173
# `dev_logging.json` is uvicorn's own log settings with its status messages, such as
# "Uvicorn running on http://127.0.0.1:8000", turned down to warnings only.
BACKEND_COMMAND: list[str] = [
    "uv",
    "run",
    "uvicorn",
    "risk_assessment.api.app:create_app",
    "--factory",
    "--port",
    str(API_PORT),
    "--log-config",
    "dev_logging.json",
]
# Vite's info lines are its address box and its "page reloaded" notes; warnings and
# errors still show.
FRONTEND_COMMAND: list[str] = [install.NPM, "run", "dev", "--", "--logLevel", "warn"]
BACKEND_READY_URL: str = f"http://127.0.0.1:{API_PORT}/api/take5/template"
# The app itself, served by Vite. Only this address is ever printed: the back end's own
# address is only the API.
LOCAL_APP_URL: str = f"http://localhost:{APP_PORT}"

# The first back-end install shows its progress. After that the sync runs quietly, so a
# start with nothing new prints nothing for it: uv still prints any error, but a pulled
# change to `uv.lock` is installed without a list of what changed.
QUIET_BACKEND_INSTALL_STEP: install.InstallStep = install.BACKEND_INSTALL_STEP._replace(
    command=[*install.BACKEND_INSTALL_STEP.command, "--quiet"],
)
# The back end's code, watched for saves so the back end can be restarted.
BACKEND_CODE: Path = BACKEND / "src"
READY_WAIT_SECONDS: float = 30.0
STOP_WAIT_SECONDS: float = 10.0

# The readiness checks ask this computer directly, never through an HTTP proxy.
_direct_opener: OpenerDirector = build_opener(ProxyHandler({}))


def port_is_busy(port: int) -> bool:
    """Say whether something on this computer already answers on a port.

    Both the IPv4 and the IPv6 address of this computer are tried, because Vite listens
    on `localhost`, which can be either. A computer with no IPv6 skips that one.

    Args:
        port: The port to try.

    Returns:
        True when a connection is accepted on either address.
    """
    for family, host in ((socket.AF_INET, "127.0.0.1"), (socket.AF_INET6, "::1")):
        try:
            with socket.socket(family, socket.SOCK_STREAM) as probe:
                probe.settimeout(0.5)
                if probe.connect_ex((host, port)) == 0:
                    return True
        except OSError:
            continue
    return False


def busy_port_message(port: int) -> str:
    """Say which port is taken and what to do about it.

    Args:
        port: The port something else is using.

    Returns:
        The message to print.
    """
    return (
        f"Something is already using port {port}. The app may already be running in "
        "another terminal: use that one, or press Ctrl+C there first. Nothing was "
        "installed or started."
    )


def app_url(environment: Mapping[str, str]) -> str:
    """Give the address to open the app at.

    In a GitHub Codespace, `localhost` is the Codespace's own computer, so the address
    is the one Codespaces forwards the port to.

    Args:
        environment: The environment variables, such as `os.environ`.

    Returns:
        The app's address, such as "http://localhost:5173".
    """
    codespace: str | None = environment.get("CODESPACE_NAME")
    domain: str | None = environment.get("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN")
    if codespace and domain:
        return f"https://{codespace}-{APP_PORT}.{domain}"
    return LOCAL_APP_URL


def ready_message(url: str) -> str:
    """Say the app is ready, where to open it, and how to stop it.

    Args:
        url: The app's address.

    Returns:
        The message, with a blank line before and after.
    """
    return f"\nThe Take 5 app is ready. Open {url}  (Ctrl+C stops it.)\n"


def frontend_needs_install(frontend: Path) -> bool:
    """Say whether the front end's packages don't match its lock file.

    Args:
        frontend: The front end's folder.

    Returns:
        True when they were never installed by this script or `install.py`, an install
        was stopped part way, or `package-lock.json` has changed since.
    """
    fingerprint_file: Path = frontend / "node_modules" / install.FRONTEND_FINGERPRINT
    if not fingerprint_file.is_file():
        return True
    return fingerprint_file.read_text(encoding="utf-8") != install.lock_fingerprint(
        frontend,
    )


def sync_backend(backend: Path) -> int:
    """Bring the back end's packages in line with `uv.lock`.

    Args:
        backend: The back end's folder.

    Returns:
        0 when it worked, otherwise uv's exit code.
    """
    if not (backend / ".venv").is_dir():
        return install.run_install_steps([install.BACKEND_INSTALL_STEP], START_COMMAND)
    result: subprocess.CompletedProcess[bytes] = subprocess.run(
        QUIET_BACKEND_INSTALL_STEP.command,
        cwd=backend,
        env=install.INSTALL_ENVIRONMENT,
        check=False,
    )
    if result.returncode != 0:
        print(
            "\nFAILED while installing "
            f"{install.BACKEND_INSTALL_STEP.what_it_installs}. Fix the problem shown "
            f"above, then run `{START_COMMAND}` again.",
        )
    return result.returncode


def install_what_changed(backend: Path, frontend: Path) -> int:
    """Bring the installs in line with the lock files, installing only what changed.

    The test browser is installed after each front-end install, so a new version of
    Playwright gets its own browser. The app doesn't need it, so when it can't be
    installed this warns and goes on.

    Args:
        backend: The back end's folder.
        frontend: The front end's folder.

    Returns:
        0 when the app can start, otherwise the exit code of the install that failed.
    """
    backend_exit_code: int = sync_backend(backend)
    if backend_exit_code != 0:
        return backend_exit_code
    if not frontend_needs_install(frontend):
        return 0
    frontend_exit_code: int = install.run_install_steps(
        [install.FRONTEND_INSTALL_STEP],
        START_COMMAND,
    )
    if frontend_exit_code != 0:
        return frontend_exit_code
    install.remember_frontend_install(frontend)
    if install.run_install_steps([install.BROWSER_INSTALL_STEP], START_COMMAND) != 0:
        print(
            "\nThe app doesn't need that browser, only the whole-app tests do, so it "
            f"starts anyway. Run `{install.INSTALL_COMMAND}` later to try again.",
            flush=True,
        )
    return 0


def start(command: list[str], folder: str) -> subprocess.Popen[bytes]:
    """Start a server in its own process group, so `stop` can stop its children too.

    What it prints goes straight to this terminal.

    Args:
        command: The server's command.
        folder: The folder, under the repo root, to run it in.

    Returns:
        The server's process.
    """
    if sys.platform == "win32":
        return subprocess.Popen(
            command,
            cwd=REPO_ROOT / folder,
            env=install.INSTALL_ENVIRONMENT,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )
    return subprocess.Popen(
        command,
        cwd=REPO_ROOT / folder,
        env=install.INSTALL_ENVIRONMENT,
        start_new_session=True,
    )


def is_local_server_ready(url: str) -> bool:
    """Ask a server on this computer, directly, whether it answers yet.

    Args:
        url: An address that answers 200 once the server is ready.

    Returns:
        True when it answered 200.
    """
    response: HTTPResponse
    with _direct_opener.open(url, timeout=1) as response:
        return response.status == 200


def wait_until_ready(
    server: subprocess.Popen[bytes],
    url: str,
    name: str,
    timeout: float = READY_WAIT_SECONDS,
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
    while time.monotonic() < deadline:
        if server.poll() is not None:
            raise RuntimeError(f"The {name} stopped before it was ready.")
        try:
            if is_local_server_ready(url):
                return
        except OSError:
            pass
        time.sleep(0.1)
    raise TimeoutError(f"The {name} did not become ready in {timeout:.0f} seconds.")


def signal_process_group(server: subprocess.Popen[bytes], signal_number: int) -> None:
    """Send a signal to a server's whole process group, on macOS and Linux.

    The group is signalled even when the server's own process has ended, since npm or
    uv can end before what they started.

    Args:
        server: The server, started in a group of its own.
        signal_number: The signal, such as `signal.SIGTERM`.
    """
    with contextlib.suppress(ProcessLookupError):  # Everything in it ended already.
        os.killpg(server.pid, signal_number)


def stop(server: subprocess.Popen[bytes]) -> None:
    """Stop a server and every process it started (npm and uv each start another).

    It asks first, then forces the stop if the server takes longer than
    `STOP_WAIT_SECONDS`, for example while a request to the AI finishes.

    Args:
        server: The server to stop.
    """
    if sys.platform == "win32":
        # Tried even when npm or uv has ended, in case what they started hasn't. Whether
        # Windows still finds the tree then is to be checked on Windows (task 0029).
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(server.pid)],
            capture_output=True,
            check=False,
        )
    else:
        signal_process_group(server, signal.SIGTERM)
    try:
        server.wait(timeout=STOP_WAIT_SECONDS)
    except subprocess.TimeoutExpired:
        if sys.platform != "win32":
            signal_process_group(server, signal.SIGKILL)
        server.kill()
        server.wait()


def stop_on_the_first_ctrl_c() -> None:
    """Make Ctrl+C stop the app once, and ignore it while the servers are stopped.

    Ctrl+C can arrive twice, because uv passes it on as well, and a second one must not
    interrupt stopping the servers and leave them running.
    """
    stopping: list[bool] = []

    def on_ctrl_c(signal_number: int, frame: FrameType | None) -> None:
        """Raise KeyboardInterrupt the first time only.

        Args:
            signal_number: The signal (SIGINT).
            frame: Where the program was; not used.

        Raises:
            KeyboardInterrupt: On the first Ctrl+C.
        """
        if not stopping:
            stopping.append(True)
            raise KeyboardInterrupt

    signal.signal(signal.SIGINT, on_ctrl_c)


def code_stamp(folder: Path) -> frozenset[tuple[str, int]]:
    """Note each Python file under a folder and when it was last saved.

    Two stamps differ when a file was saved, added, removed or renamed.

    Args:
        folder: The folder to look in, such as `backend/src`.

    Returns:
        Each file's path with its last-saved time in nanoseconds.
    """
    stamp: set[tuple[str, int]] = set()
    for path in folder.rglob("*.py"):
        with contextlib.suppress(OSError):  # Removed while being looked at.
            stamp.add((str(path), path.stat().st_mtime_ns))
    return frozenset(stamp)


def restart_backend(
    servers: dict[str, subprocess.Popen[bytes]],
    timeout: float = READY_WAIT_SECONDS,
) -> bool:
    """Stop the back end and start it again with the code just saved.

    Args:
        servers: The running servers by name; the new back end replaces the old one.
        timeout: Seconds to wait for the new back end to answer.

    Returns:
        True when it answers; False when it stopped or didn't answer, after saying so.
    """
    print("\nA back-end file changed, so the back end is restarting.", flush=True)
    stop(servers["back end"])
    servers["back end"] = start(BACKEND_COMMAND, "backend")
    try:
        wait_until_ready(servers["back end"], BACKEND_READY_URL, "back end", timeout)
    except (RuntimeError, TimeoutError) as problem:
        print(
            f"\n{problem} Its error is above. The app is waiting: save a fix and the "
            "back end starts again.",
            flush=True,
        )
        return False
    print("The back end is running again.", flush=True)
    return True


def run_servers(url: str, cloud_service: str | None) -> int:
    """Run both servers until either one stops or Ctrl+C is pressed, then stop both.

    Args:
        url: The app's address, to print once it is ready.
        cloud_service: The sync service whose folder holds the repo, if any, so its
            warning shows again under the ready line.

    Returns:
        0 after Ctrl+C, otherwise 1 when a server didn't start or stopped by itself.
    """
    servers: dict[str, subprocess.Popen[bytes]] = {}
    stop_on_the_first_ctrl_c()
    try:
        servers["back end"] = start(BACKEND_COMMAND, "backend")
        wait_until_ready(servers["back end"], BACKEND_READY_URL, "back end")
        servers["front end"] = start(FRONTEND_COMMAND, "frontend")
        wait_until_ready(servers["front end"], LOCAL_APP_URL, "front end")
        print(ready_message(url), flush=True)
        if cloud_service is not None:
            print(f"{install.cloud_sync_warning(cloud_service)}\n", flush=True)
        backend_code: frozenset[tuple[str, int]] = code_stamp(BACKEND_CODE)
        backend_waits_for_a_fix: bool = False
        while True:
            saved_code: frozenset[tuple[str, int]] = code_stamp(BACKEND_CODE)
            if saved_code != backend_code:
                backend_code = saved_code
                backend_waits_for_a_fix = not restart_backend(servers)
            for name, server in servers.items():
                if name == "back end" and backend_waits_for_a_fix:
                    continue
                exit_code: int | None = server.poll()
                if exit_code is not None:
                    print(
                        f"\nThe {name} stopped (exit code {exit_code}), so the app was "
                        f"stopped. Check its output above, then run `{START_COMMAND}` "
                        "again.",
                        flush=True,
                    )
                    return 1
            time.sleep(1)
    except (RuntimeError, TimeoutError) as problem:
        print(
            f"\n{problem} Check its output above, fix the problem, then run "
            f"`{START_COMMAND}` again.",
            flush=True,
        )
        return 1
    except KeyboardInterrupt:
        return 0
    finally:
        # Once stopping has begun, Ctrl+C can't interrupt it, whatever began it.
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        for server in servers.values():
            stop(server)


def main() -> int:
    """Check, install what changed, and run the app until Ctrl+C.

    Returns:
        The exit code: 0 after Ctrl+C, otherwise non-zero.
    """
    cloud_service: str | None = install.cloud_sync_service(REPO_ROOT)
    if cloud_service is not None:
        print(install.cloud_sync_warning(cloud_service), flush=True)
    for port in (API_PORT, APP_PORT):
        if port_is_busy(port):
            print(busy_port_message(port))
            return 1
    problems: list[str] = install.missing_tools()
    if problems:
        print("\nThe app can't start yet. Nothing was installed.")
        for problem in problems:
            print(f"  - {problem}")
        print(install.REOPEN_TERMINAL_HELP)
        return 1
    install_exit_code: int = install_what_changed(BACKEND, FRONTEND)
    if install_exit_code != 0:
        return install_exit_code
    return run_servers(app_url(os.environ), cloud_service)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nStopped before the app started.")
        sys.exit(130)
