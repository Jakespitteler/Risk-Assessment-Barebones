# /// script
# requires-python = ">=3.13"
# ///
"""Set up what isn't set up yet, bring the installs in line, and start the app.

Usage, from the repo root: `uv run start.py`, then open the one address it prints.
Press Ctrl+C to stop it. Both halves restart by themselves when their code changes.

In order, it:

1. Stops if ports 8000 or 5173 are already in use, before installing anything, since the
   app is probably running in another terminal.
2. Checks for git and Node.js, as `setup.py` does.
3. Brings the installs in line with the lock files the repo holds: the back end's
   packages every time (quick when nothing changed), the front end's only when
   `package-lock.json` changed since they were installed, and then the browser the
   whole-app tests use. It installs exactly the locked versions and never upgrades one.
4. Starts the back end, then the front end, passing on what they print except the lines
   that give their own addresses, and prints the app's address once it answers.
"""

import contextlib
import os
import re
import signal
import socket
import subprocess
import sys
import threading
import time
from collections.abc import Iterable, Mapping
from http.client import HTTPResponse
from pathlib import Path
from types import FrameType
from typing import IO
from urllib.request import OpenerDirector, ProxyHandler, build_opener

import setup

REPO_ROOT: Path = Path(__file__).resolve().parent
BACKEND: Path = REPO_ROOT / "backend"
FRONTEND: Path = REPO_ROOT / "frontend"
START_COMMAND: str = "uv run start.py"

API_PORT: int = 8000
APP_PORT: int = 5173
BACKEND_COMMAND: list[str] = [
    "uv",
    "run",
    "uvicorn",
    "risk_assessment.api.app:create_app",
    "--factory",
    "--reload",
    "--port",
    str(API_PORT),
]
FRONTEND_COMMAND: list[str] = [setup.NPM, "run", "dev"]
BACKEND_READY_URL: str = f"http://127.0.0.1:{API_PORT}/api/take5/template"
# The app itself, served by Vite. Only this address is ever printed: the back end's own
# address is only the API.
LOCAL_APP_URL: str = f"http://localhost:{APP_PORT}"

# The first back-end install shows its progress. After that the sync runs quietly, so a
# start with nothing new prints nothing for it: uv still prints any error, but a pulled
# change to `uv.lock` is installed without a list of what changed.
FIRST_BACKEND_INSTALL: setup.InstallStep = setup.INSTALL_STEPS[0]
BACKEND_INSTALL: setup.InstallStep = FIRST_BACKEND_INSTALL._replace(
    command=[*FIRST_BACKEND_INSTALL.command, "--quiet"],
)
FRONTEND_INSTALL: setup.InstallStep = setup.INSTALL_STEPS[1]
BROWSER_INSTALL: setup.InstallStep = setup.INSTALL_STEPS[2]

# What uvicorn and Vite print about their own addresses: uvicorn's "running on" line and
# Vite's banner. Colour codes are removed before a line is matched.
ADDRESS_LINE: re.Pattern[str] = re.compile(
    r"Uvicorn running on "
    r"|\bLocal:\s|\bNetwork:\s|press h \+ enter|VITE v\S+\s+ready in",
)
COLOUR_CODE: re.Pattern[str] = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
READY_WAIT_SECONDS: float = 30.0
STOP_WAIT_SECONDS: float = 10.0
OUTPUT_WAIT_SECONDS: float = 2.0

# One server's lines and this script's own never interleave mid-line.
_output_lock: threading.Lock = threading.Lock()
# The thread passing on each server's output, so it can be waited for.
_output_readers: dict[subprocess.Popen[bytes], threading.Thread] = {}
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
        True when they were never installed by this script or `setup.py`, an install
        was stopped part way, or `package-lock.json` has changed since.
    """
    fingerprint_file: Path = frontend / "node_modules" / setup.FRONTEND_FINGERPRINT
    if not fingerprint_file.is_file():
        return True
    return fingerprint_file.read_text(encoding="utf-8") != setup.lock_fingerprint(
        frontend,
    )


def browser_needs_install(frontend: Path) -> bool:
    """Say whether the whole-app tests' browser needs installing.

    It is installed after every front-end install, so a new version of Playwright gets
    its own browser.

    Args:
        frontend: The front end's folder.

    Returns:
        True when it hasn't been installed since the last front-end install.
    """
    return not (frontend / "node_modules" / setup.BROWSER_MARKER).is_file()


def sync_backend(backend: Path) -> int:
    """Bring the back end's packages in line with `uv.lock`.

    Args:
        backend: The back end's folder.

    Returns:
        0 when it worked, otherwise uv's exit code.
    """
    if not (backend / ".venv").is_dir():
        return setup.install([FIRST_BACKEND_INSTALL], START_COMMAND)
    result: subprocess.CompletedProcess[bytes] = subprocess.run(
        BACKEND_INSTALL.command,
        cwd=backend,
        env=setup.SETUP_ENVIRONMENT,
        check=False,
    )
    if result.returncode != 0:
        print(
            f"\nFAILED while installing {BACKEND_INSTALL.what_it_installs}. Fix the "
            f"problem shown above, then run `{START_COMMAND}` again.",
        )
    return result.returncode


def install_what_changed(backend: Path, frontend: Path) -> int:
    """Bring the installs in line with the lock files, installing only what changed.

    The browser is only for the tests, so when it can't be installed this warns and goes
    on, and the next start tries again.

    Args:
        backend: The back end's folder.
        frontend: The front end's folder.

    Returns:
        0 when the app can start, otherwise the exit code of the install that failed.
    """
    backend_exit_code: int = sync_backend(backend)
    if backend_exit_code != 0:
        return backend_exit_code
    if frontend_needs_install(frontend):
        exit_code: int = setup.install([FRONTEND_INSTALL], START_COMMAND)
        if exit_code != 0:
            return exit_code
        setup.remember_frontend_install(frontend)
    if browser_needs_install(frontend):
        if setup.install([BROWSER_INSTALL], START_COMMAND) == 0:
            setup.remember_browser_install(frontend)
        else:
            print(
                "\nThe app doesn't need that browser, only the whole-app tests do, so "
                "it starts anyway. The next start tries again.",
                flush=True,
            )
    return 0


def visible_text(line: bytes) -> str:
    """Read a line a server printed as text, without its colour codes.

    Args:
        line: One line of output, which may hold colour codes.

    Returns:
        The line's text, as a person sees it.
    """
    return COLOUR_CODE.sub("", line.decode("utf-8", errors="replace"))


def is_address_line(line: bytes) -> bool:
    """Say whether a line a server printed gives the server's own address.

    Args:
        line: One line of output, which may hold colour codes.

    Returns:
        True for uvicorn's "running on" line and the lines of Vite's banner.
    """
    return ADDRESS_LINE.search(visible_text(line)) is not None


def write_line(line: bytes, terminal: IO[bytes]) -> None:
    """Write one whole line to the terminal, without splitting another's.

    Args:
        line: The line, ending with its line break.
        terminal: Where to write it, such as `sys.stdout.buffer`.
    """
    with _output_lock:
        terminal.write(line)
        terminal.flush()


def say(message: str) -> None:
    """Print one of this script's own messages once servers are printing too.

    Args:
        message: What to say.
    """
    sys.stdout.flush()
    write_line(f"{message}\n".encode(), sys.stdout.buffer)


def pass_on_output(lines: Iterable[bytes], terminal: IO[bytes]) -> None:
    """Pass a server's output on to the terminal, leaving out its address lines.

    Each line goes on unchanged, colours and all, as soon as it arrives. A blank line
    straight after another blank line or an address line is left out too, so Vite's
    banner leaves no gap behind.

    Args:
        lines: The server's output, one line at a time.
        terminal: Where to write it.
    """
    after_gap: bool = True
    for line in lines:
        if is_address_line(line):
            after_gap = True
            continue
        is_blank: bool = not visible_text(line).strip()
        if is_blank and after_gap:
            continue
        write_line(line, terminal)
        after_gap = is_blank


def server_environment(in_colour: bool) -> dict[str, str]:
    """Build the environment the servers run in.

    Args:
        in_colour: Whether this script prints to a terminal, so the servers should keep
            their colours though their output goes through a pipe.

    Returns:
        This script's environment, without its own `VIRTUAL_ENV` (the back end uses its
        own `.venv`), and with Python's output sent at once and in UTF-8 (Windows would
        otherwise write a pipe in its own code page).
    """
    environment: dict[str, str] = {
        **setup.SETUP_ENVIRONMENT,
        "PYTHONUNBUFFERED": "1",
        "PYTHONUTF8": "1",
    }
    if in_colour:
        environment["FORCE_COLOR"] = "1"
    return environment


def start(
    command: list[str],
    folder: str,
    environment: Mapping[str, str],
) -> subprocess.Popen[bytes]:
    """Start a server in its own process group, passing on what it prints.

    Its own process group lets `stop` stop everything it starts too.

    Args:
        command: The server's command.
        folder: The folder, under the repo root, to run it in.
        environment: The environment to run it in.

    Returns:
        The server's process.
    """
    server: subprocess.Popen[bytes]
    if sys.platform == "win32":
        server = subprocess.Popen(
            command,
            cwd=REPO_ROOT / folder,
            env=dict(environment),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )
    else:
        server = subprocess.Popen(
            command,
            cwd=REPO_ROOT / folder,
            env=dict(environment),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    if server.stdout is not None:
        reader: threading.Thread = threading.Thread(
            target=pass_on_output,
            args=(server.stdout, sys.stdout.buffer),
            daemon=True,
        )
        reader.start()
        _output_readers[server] = reader
    return server


def wait_for_output(servers: Iterable[subprocess.Popen[bytes]]) -> None:
    """Let the servers' last lines reach the terminal, such as an error's traceback.

    Called once they have stopped, before saying why, and before this script exits.

    Args:
        servers: The servers whose output to wait for.
    """
    for server in servers:
        reader: threading.Thread | None = _output_readers.get(server)
        if reader is not None:
            reader.join(timeout=OUTPUT_WAIT_SECONDS)


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
        if server.poll() is None:
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


def run_servers(url: str, cloud_service: str | None) -> int:
    """Run both servers until either one stops or Ctrl+C is pressed, then stop both.

    Args:
        url: The app's address, to print once it is ready.
        cloud_service: The sync service whose folder holds the repo, if any, so its
            warning shows again under the ready line.

    Returns:
        0 after Ctrl+C, otherwise 1 when a server didn't start or stopped by itself.
    """
    in_colour: bool = sys.stdout.isatty()
    environment: dict[str, str] = server_environment(in_colour)
    backend_command: list[str] = BACKEND_COMMAND
    if in_colour:
        backend_command = [*BACKEND_COMMAND, "--use-colors"]
    servers: dict[str, subprocess.Popen[bytes]] = {}
    stop_on_the_first_ctrl_c()
    try:
        servers["back end"] = start(backend_command, "backend", environment)
        wait_until_ready(servers["back end"], BACKEND_READY_URL, "back end")
        servers["front end"] = start(FRONTEND_COMMAND, "frontend", environment)
        wait_until_ready(servers["front end"], LOCAL_APP_URL, "front end")
        say(ready_message(url))
        if cloud_service is not None:
            say(f"{setup.cloud_sync_warning(cloud_service)}\n")
        while True:
            for name, server in servers.items():
                exit_code: int | None = server.poll()
                if exit_code is not None:
                    wait_for_output([server])
                    say(
                        f"\nThe {name} stopped (exit code {exit_code}), so the app was "
                        f"stopped. Check its output above, then run `{START_COMMAND}` "
                        "again.",
                    )
                    return 1
            time.sleep(1)
    except (RuntimeError, TimeoutError) as problem:
        wait_for_output(
            server for server in servers.values() if server.poll() is not None
        )
        say(
            f"\n{problem} Check its output above, fix the problem, then run "
            f"`{START_COMMAND}` again.",
        )
        return 1
    except KeyboardInterrupt:
        return 0
    finally:
        for server in servers.values():
            stop(server)
        wait_for_output(servers.values())


def main() -> int:
    """Check, install what changed, and run the app until Ctrl+C.

    Returns:
        The exit code: 0 after Ctrl+C, otherwise non-zero.
    """
    cloud_service: str | None = setup.cloud_sync_service(REPO_ROOT)
    if cloud_service is not None:
        print(setup.cloud_sync_warning(cloud_service), flush=True)
    for port in (API_PORT, APP_PORT):
        if port_is_busy(port):
            print(busy_port_message(port))
            return 1
    problems: list[str] = setup.missing_tools()
    if problems:
        print("\nThe app can't start yet. Nothing was installed.")
        for problem in problems:
            print(f"  - {problem}")
        print(setup.REOPEN_TERMINAL_HELP)
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
