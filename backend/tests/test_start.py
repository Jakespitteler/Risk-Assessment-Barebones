"""Tests for `start.py`: checking, installing what changed, and starting both halves."""

import copy
import json
import os
import signal
import socket
import subprocess
from collections.abc import Iterator
from pathlib import Path, PureWindowsPath
from typing import Any
from unittest.mock import MagicMock, call, patch
from urllib.error import URLError

import pytest
import start
import uvicorn.config


@pytest.fixture(autouse=True)
def running_file(tmp_path: Path) -> Iterator[Path]:
    """Keep start.py's process-ID file out of the repo during tests.

    Args:
        tmp_path: A folder for this test.

    Yields:
        Where start.py writes its process ID in this test.
    """
    path: Path = tmp_path / ".start.pid"
    with patch.object(start, "RUNNING_FILE", path):
        yield path


def make_backend(folder: Path) -> Path:
    """Make a stand-in back-end folder that has been installed before.

    Args:
        folder: Where to make it.

    Returns:
        The back end's folder.
    """
    backend: Path = folder / "backend"
    (backend / ".venv").mkdir(parents=True)
    return backend


def make_frontend(folder: Path, lock_text: str = '{"lockfileVersion": 3}') -> Path:
    """Make a stand-in front-end folder holding only a lock file.

    Args:
        folder: Where to make it.
        lock_text: What `package-lock.json` holds.

    Returns:
        The front end's folder.
    """
    frontend: Path = folder / "frontend"
    frontend.mkdir()
    (frontend / "package-lock.json").write_text(lock_text, encoding="utf-8")
    return frontend


def mark_installed(frontend: Path) -> None:
    """Make the front end look installed for its current lock file.

    Args:
        frontend: The stand-in front-end folder.
    """
    node_modules: Path = frontend / "node_modules"
    node_modules.mkdir()
    (node_modules / start.install.FRONTEND_FINGERPRINT).write_text(
        start.install.lock_fingerprint(frontend),
        encoding="utf-8",
    )


def only_the_app_port_is_busy(port: int) -> bool:
    """Stand in for the port check when only Vite's port is taken.

    Args:
        port: The port being checked.
    """
    return port == start.APP_PORT


def test_a_port_something_listens_on_is_busy_and_a_closed_one_is_free() -> None:
    """A real listening socket is found; once it closes, the port is free again."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        port: int = listener.getsockname()[1]

        assert start.port_is_busy(port)

    assert not start.port_is_busy(port)


def test_a_busy_port_stops_it_before_anything_is_installed(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """With 5173 taken it says the app may be running, and installs nothing."""
    with (
        patch.object(start.install, "cloud_sync_service", return_value=None),
        patch.object(start, "port_is_busy", side_effect=only_the_app_port_is_busy),
        patch.object(start, "listening_pids", return_value=set()),
        patch.object(start.install, "missing_tools") as missing_tools,
        patch.object(start, "install_what_changed") as install,
        patch.object(start, "run_servers") as run_servers,
    ):
        exit_code: int = start.main()

    assert exit_code == 1
    assert capsys.readouterr().out.strip() == start.busy_port_message(5173)
    assert "already be running in another terminal" in start.busy_port_message(5173)
    missing_tools.assert_not_called()
    install.assert_not_called()
    run_servers.assert_not_called()


NETSTAT: str = """
Active Connections

  Proto  Local Address          Foreign Address        State           PID
  TCP    0.0.0.0:135            0.0.0.0:0              LISTENING       1044
  TCP    127.0.0.1:8000         0.0.0.0:0              LISTENING       5120
  TCP    127.0.0.1:8000         127.0.0.1:61234        ESTABLISHED     5120
  TCP    127.0.0.1:18000        0.0.0.0:0              LISTENING       9999
  TCP    [::1]:5173             [::]:0                 LISTENING       7344
  TCP    [::1]:5173             [::1]:61240            ESTABLISHED     7344
  TCP    [::]:3000              [::]:0                 ABHÖREN         2020
  UDP    0.0.0.0:5173           *:*                                    6060
"""


def test_windows_listeners_are_read_from_netstat() -> None:
    """Listening sockets on exactly that port count, on IPv4 or IPv6 (task 0044).

    A listening socket has no remote end, which netstat shows the same in every
    language, while the state's name is translated (here German).
    """
    assert start.windows_listeners(NETSTAT, 8000) == {5120}
    assert start.windows_listeners(NETSTAT, 5173) == {7344}
    assert start.windows_listeners(NETSTAT, 3000) == {2020}
    assert start.windows_listeners(NETSTAT, 4000) == set()


# cspell:ignore retrnsmt ABHÖREN
def made_up_proc(folder: Path, port: int, pid: int) -> Path:
    """Make a /proc with one process listening on a port.

    Args:
        folder: Where to make it.
        port: The port it listens on.
        pid: Its process ID.

    Returns:
        The made-up /proc.
    """
    proc: Path = folder / "proc"
    (proc / "net").mkdir(parents=True)
    header: str = "  sl  local_address rem_address   st tx_queue rx_queue tr tm->when "
    header += "retrnsmt   uid  timeout inode\n"
    (proc / "net" / "tcp").write_text(
        header
        + f"   0: 0100007F:{port:04X} 00000000:0000 0A 00000000:00000000 00:00000000 "
        "00000000  1000        0 424242 1 0000000000000000 100 0 0 10 0\n"
        + f"   1: 0100007F:{port:04X} 0100007F:D431 01 00000000:00000000 00:00000000 "
        "00000000  1000        0 515151 1 0000000000000000 20 4 30 10 -1\n",
        encoding="ascii",
    )
    fd: Path = proc / str(pid) / "fd"
    fd.mkdir(parents=True)
    (fd / "3").symlink_to("socket:[424242]")
    (proc / str(pid) / "cmdline").write_bytes(b"node\0vite.js\0")
    other: Path = proc / "99" / "fd"
    other.mkdir(parents=True)
    (other / "3").symlink_to("socket:[515151]")
    return proc


def test_linux_listeners_are_found_in_proc(tmp_path: Path) -> None:
    """The listening socket's inode leads to its process; a connection doesn't count."""
    proc: Path = made_up_proc(tmp_path, 5173, 4321)

    assert start.linux_listeners(proc, 5173) == {4321}
    assert start.linux_listeners(proc, 8000) == set()
    assert start.command_line(4321, proc) == "node vite.js "


BACK_END: str = (
    "/repo/backend/.venv/bin/python /repo/backend/.venv/bin/uvicorn "
    "risk_assessment.api.app:create_app --factory --port 8000 "
    "--log-config dev_logging.json"
)
VITE: str = "node /repo/frontend/node_modules/.bin/vite --logLevel warn"


@pytest.mark.parametrize(
    ("command", "ours"),
    [
        (BACK_END, True),
        (VITE, True),
        (
            "node /repo/frontend/node_modules/.bin/../vite/bin/vite.js --logLevel warn",
            True,
        ),
        (BACK_END.removesuffix(" --log-config dev_logging.json"), False),
        (VITE.removesuffix(" --logLevel warn"), False),
        (VITE.replace("/repo/", "/repo-old/"), False),
        (BACK_END.replace("/repo/", "/repo/.claude/worktrees/agent-1/"), False),
        ("python -m http.server 8000 --directory /repo/docs/invite", False),
        (
            "/repo/backend/.venv/bin/python -m pytest -k uvicorn dev_logging.json",
            False,
        ),
        ("/elsewhere/.venv/bin/uvicorn other.app:app --port 8000", False),
        ("", False),
    ],
    ids=[
        "back_end",
        "vite",
        "vite_script",
        "whole_app_tests_back_end",
        "whole_app_tests_vite",
        "another_copy_of_the_repo",
        "a_worktree_inside_the_repo",
        "a_word_holding_vite",
        "uvicorn_as_a_word",
        "uvicorn_elsewhere",
        "unknown",
    ],
)
def test_only_this_apps_back_end_and_vite_are_recognised(
    command: str,
    ours: bool,
) -> None:
    """Only start.py's own uvicorn or Vite, run from this folder (task 0044)."""
    assert start.is_this_apps(command, Path("/repo")) is ours


def test_a_windows_command_line_is_matched_ignoring_case() -> None:
    """Windows paths have backslashes, may hold spaces, and ignore case."""
    repo: PureWindowsPath = PureWindowsPath("C:/Users/Sam Example/Risk Assessment")
    scripts: str = f"{repo}\\BACKEND\\.venv\\Scripts"
    command: str = (
        f'"{scripts}\\python.exe" "{scripts}\\uvicorn.exe" '
        "risk_assessment.api.app:create_app --log-config dev_logging.json"
    )
    with patch.object(start.sys, "platform", "win32"):
        assert start.is_this_apps(command, repo)
        assert not start.is_this_apps(command.replace("Risk ", "Old Risk "), repo)


def test_a_leftover_copy_of_the_app_is_stopped_and_the_app_starts(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A port held only by this app's leftover is freed, then all goes on (0044)."""
    busy: list[bool] = [True, False]

    def api_port_busy_once(port: int) -> bool:
        """Say the back end's port is busy until the leftover is stopped.

        Args:
            port: The port being checked.
        """
        return port == start.API_PORT and busy.pop(0)

    with (
        patch.object(start.install, "cloud_sync_service", return_value=None),
        patch.object(
            start,
            "port_is_busy",
            side_effect=api_port_busy_once,
        ),
        patch.object(start, "listening_pids", return_value={5120}),
        patch.object(
            start,
            "command_line",
            return_value=BACK_END.replace("/repo", str(start.REPO_ROOT)),
        ),
        patch.object(start, "stop_leftover") as stop_leftover,
        patch.object(start.install, "missing_tools", return_value=[]),
        patch.object(start, "install_what_changed", return_value=0),
        patch.object(start, "run_servers", return_value=0) as run_servers,
    ):
        exit_code: int = start.main()

    assert exit_code == 0
    stop_leftover.assert_called_once_with(5120, force=False)
    run_servers.assert_called_once()
    assert "left running on port 8000; stopping it." in capsys.readouterr().out


def test_another_program_on_the_port_is_never_stopped(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Something that isn't this app keeps its port, and the app says what to do."""
    with (
        patch.object(start.install, "cloud_sync_service", return_value=None),
        patch.object(start, "port_is_busy", side_effect=only_the_app_port_is_busy),
        patch.object(start, "listening_pids", return_value={7344}),
        patch.object(start, "command_line", return_value="C:\\Games\\server.exe"),
        patch.object(start, "stop_leftover") as stop_leftover,
        patch.object(start, "install_what_changed") as install,
    ):
        exit_code: int = start.main()

    assert exit_code == 1
    stop_leftover.assert_not_called()
    install.assert_not_called()
    assert capsys.readouterr().out.strip() == start.busy_port_message(5173)


def test_a_leftover_that_wont_stop_leaves_the_message(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """If the port is still taken after the wait, nothing is installed or started."""
    with (
        patch.object(start.install, "cloud_sync_service", return_value=None),
        patch.object(start, "port_is_busy", side_effect=only_the_app_port_is_busy),
        patch.object(start, "listening_pids", return_value={7344}),
        patch.object(
            start,
            "command_line",
            return_value=VITE.replace("/repo", str(start.REPO_ROOT)),
        ),
        patch.object(start, "stop_leftover") as stop_leftover,
        patch.object(start, "FREE_PORT_WAIT_SECONDS", 0.01),
        patch.object(start, "install_what_changed") as install,
    ):
        exit_code: int = start.main()

    assert exit_code == 1
    assert stop_leftover.call_args_list == [
        call(7344, force=False),
        call(7344, force=True),
    ]
    install.assert_not_called()
    assert start.busy_port_message(5173) in capsys.readouterr().out


def test_a_copy_whose_start_py_still_runs_is_left_alone(
    running_file: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The app running in another terminal isn't a leftover, so it keeps its port."""
    running_file.write_text("4242", encoding="ascii")

    def command_line(pid: int) -> str:
        """Say what each process runs: 4242 is the other start.py.

        Args:
            pid: The process's ID.
        """
        if pid == 4242:  # noqa: PLR2004 - the other start.py
            return "python start.py"
        return VITE.replace("/repo", str(start.REPO_ROOT))

    with (
        patch.object(start.install, "cloud_sync_service", return_value=None),
        patch.object(start, "port_is_busy", side_effect=only_the_app_port_is_busy),
        patch.object(start, "listening_pids", return_value={7344}),
        patch.object(start, "command_line", side_effect=command_line),
        patch.object(start, "stop_leftover") as stop_leftover,
        patch.object(start, "install_what_changed") as install,
    ):
        exit_code: int = start.main()

    assert exit_code == 1
    stop_leftover.assert_not_called()
    install.assert_not_called()
    assert capsys.readouterr().out.strip() == start.busy_port_message(5173)
    assert running_file.read_text(encoding="ascii") == "4242"


def test_a_port_shared_with_another_program_is_never_freed() -> None:
    """Every listener must be this app's; one other program keeps the port."""
    vite: str = VITE.replace("/repo", str(start.REPO_ROOT))
    with (
        patch.object(start, "listening_pids", return_value={7344, 8080}),
        patch.object(start, "command_line", side_effect=[vite, "nginx"]),
        patch.object(start, "stop_leftover") as stop_leftover,
    ):
        assert not start.free_port(5173)

    stop_leftover.assert_not_called()


def test_the_running_file_is_written_while_it_runs_and_removed_after(
    running_file: Path,
) -> None:
    """A second start.py can tell this one runs; the file goes when it stops."""
    seen: list[str] = []

    def run_servers(_url: str, _cloud_service: str | None) -> int:
        """Note what the file holds while the app runs.

        Returns:
            0, as after Ctrl+C.
        """
        seen.append(running_file.read_text(encoding="ascii"))
        return 0

    running_file.write_text("999999", encoding="ascii")
    with (
        patch.object(start.install, "cloud_sync_service", return_value=None),
        patch.object(start, "port_is_busy", return_value=False),
        patch.object(start.install, "missing_tools", return_value=[]),
        patch.object(start, "install_what_changed", return_value=0),
        patch.object(start, "run_servers", side_effect=run_servers),
    ):
        assert start.main() == 0

    assert seen == [str(os.getpid())]
    assert not running_file.exists()
    assert not start.another_start_is_running(running_file)


@pytest.mark.skipif(not Path("/proc/net/tcp").exists(), reason="Linux's /proc only")
def test_a_real_listener_is_found_with_its_command_line() -> None:
    """On Linux, the real /proc finds this test's own listening socket and process."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        port: int = listener.getsockname()[1]

        assert os.getpid() in start.listening_pids(port)
        assert "python" in start.command_line(os.getpid()).casefold()


def test_a_missing_tool_stops_it_before_anything_is_installed(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The same check and help as `install.py`, before any install."""
    with (
        patch.object(start.install, "cloud_sync_service", return_value=None),
        patch.object(start, "port_is_busy", return_value=False),
        patch.object(start.install, "missing_tools", return_value=["git is missing."]),
        patch.object(start, "install_what_changed") as install,
    ):
        exit_code: int = start.main()

    output: str = capsys.readouterr().out
    assert exit_code == 1
    assert "  - git is missing." in output
    assert start.install.REOPEN_TERMINAL_HELP in output
    install.assert_not_called()


def test_a_failed_install_stops_it_before_the_servers_start() -> None:
    """The install's exit code is passed on, and nothing is started."""
    with (
        patch.object(start.install, "cloud_sync_service", return_value=None),
        patch.object(start, "port_is_busy", return_value=False),
        patch.object(start.install, "missing_tools", return_value=[]),
        patch.object(start, "install_what_changed", return_value=4),
        patch.object(start, "run_servers") as run_servers,
    ):
        exit_code: int = start.main()

    assert exit_code == 4
    run_servers.assert_not_called()


def test_the_app_address_is_localhost_on_a_computer() -> None:
    """Away from Codespaces it is Vite's address, never the API's port 8000."""
    url: str = start.app_url({})

    assert url == "http://localhost:5173"
    assert "8000" not in start.ready_message(url)


def test_the_app_address_in_a_codespace_is_the_forwarded_one() -> None:
    """Codespaces forwards port 5173 to an address of its own."""
    url: str = start.app_url(
        {
            "CODESPACE_NAME": "example-space-abc123",
            "GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN": "app.github.dev",
        },
    )

    assert url == "https://example-space-abc123-5173.app.github.dev"


def test_the_ready_line_names_the_address_and_how_to_stop() -> None:
    """One line: the app is ready, where to open it, and Ctrl+C."""
    message: str = start.ready_message("http://localhost:5173")

    assert message.strip() == (
        "The Take 5 app is ready. Open http://localhost:5173  (Ctrl+C stops it.)"
    )


def test_a_front_end_never_installed_here_needs_installing(tmp_path: Path) -> None:
    """No node_modules, or one with no fingerprint (a stopped install), installs."""
    frontend: Path = make_frontend(tmp_path)
    assert start.frontend_needs_install(frontend)

    (frontend / "node_modules").mkdir()
    assert start.frontend_needs_install(frontend)


def test_a_front_end_installed_for_this_lock_file_needs_nothing(
    tmp_path: Path,
) -> None:
    """The fingerprint matches the lock file, so nothing is installed."""
    frontend: Path = make_frontend(tmp_path)
    mark_installed(frontend)

    assert not start.frontend_needs_install(frontend)


def test_a_changed_lock_file_needs_installing(tmp_path: Path) -> None:
    """After a pull that changes package-lock.json, the front end is installed again."""
    frontend: Path = make_frontend(tmp_path)
    mark_installed(frontend)
    (frontend / "package-lock.json").write_text('{"changed": true}', encoding="utf-8")

    assert start.frontend_needs_install(frontend)


def test_nothing_changed_runs_only_the_quick_back_end_sync(tmp_path: Path) -> None:
    """Uv's sync with the lock file runs every time; npm and Playwright don't."""
    frontend: Path = make_frontend(tmp_path)
    mark_installed(frontend)
    with (
        patch.object(
            start.subprocess,
            "run",
            return_value=subprocess.CompletedProcess([], 0),
        ) as run,
        patch.object(start.install, "run_install_steps") as install,
    ):
        exit_code: int = start.install_what_changed(make_backend(tmp_path), frontend)

    assert exit_code == 0
    run.assert_called_once_with(
        ["uv", "sync", "--locked", "--quiet"],
        cwd=tmp_path / "backend",
        env=start.install.INSTALL_ENVIRONMENT,
        check=False,
    )
    install.assert_not_called()


def test_the_first_back_end_install_shows_its_progress(tmp_path: Path) -> None:
    """With no `.venv` yet, uv's install runs under a heading, not quietly."""
    frontend: Path = make_frontend(tmp_path)
    mark_installed(frontend)
    with patch.object(start.install, "run_install_steps", return_value=0) as install:
        exit_code: int = start.install_what_changed(tmp_path / "backend", frontend)

    assert exit_code == 0
    install.assert_called_once_with(
        [start.install.BACKEND_INSTALL_STEP],
        "uv run start.py",
    )
    assert "--quiet" not in start.install.BACKEND_INSTALL_STEP.command


def test_a_changed_lock_file_installs_the_front_end_then_the_browser(
    tmp_path: Path,
) -> None:
    """`npm ci` (exact versions), then the test browser; the install is remembered."""
    frontend: Path = make_frontend(tmp_path)

    def install_succeeds(steps: list[object], rerun_command: str) -> int:
        """Stand in for an install: npm makes node_modules, then it succeeds."""
        (frontend / "node_modules").mkdir(exist_ok=True)
        return 0

    with (
        patch.object(
            start.subprocess,
            "run",
            return_value=subprocess.CompletedProcess([], 0),
        ),
        patch.object(
            start.install,
            "run_install_steps",
            side_effect=install_succeeds,
        ) as install,
    ):
        exit_code: int = start.install_what_changed(make_backend(tmp_path), frontend)

    assert exit_code == 0
    assert install.mock_calls == [
        call([start.install.FRONTEND_INSTALL_STEP], "uv run start.py"),
        call([start.install.BROWSER_INSTALL_STEP], "uv run start.py"),
    ]
    assert start.install.FRONTEND_INSTALL_STEP.command[1:] == ["ci", "--engine-strict"]
    assert not start.frontend_needs_install(frontend)


def test_installs_never_upgrade_a_package() -> None:
    """Every install takes the lock files' versions exactly (task 0029, question 3)."""
    commands: list[list[str]] = [
        start.QUIET_BACKEND_INSTALL_STEP.command,
        start.install.FRONTEND_INSTALL_STEP.command,
        start.install.BROWSER_INSTALL_STEP.command,
    ]

    assert "--locked" in start.QUIET_BACKEND_INSTALL_STEP.command
    assert start.install.FRONTEND_INSTALL_STEP.command[1] == "ci"
    assert not any(
        "upgrade" in word or "update" in word for c in commands for word in c
    )


def test_a_failed_front_end_install_is_not_remembered(tmp_path: Path) -> None:
    """The exit code is passed on, and the next start tries again."""
    frontend: Path = make_frontend(tmp_path)
    with (
        patch.object(
            start.subprocess,
            "run",
            return_value=subprocess.CompletedProcess([], 0),
        ),
        patch.object(start.install, "run_install_steps", return_value=1),
    ):
        exit_code: int = start.install_what_changed(make_backend(tmp_path), frontend)

    assert exit_code == 1
    assert start.frontend_needs_install(frontend)


def test_a_failed_back_end_sync_stops_it(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """It says what failed and to run `uv run start.py` again."""
    frontend: Path = make_frontend(tmp_path)
    with (
        patch.object(
            start.subprocess,
            "run",
            return_value=subprocess.CompletedProcess([], 2),
        ),
        patch.object(start.install, "run_install_steps") as install,
    ):
        exit_code: int = start.install_what_changed(make_backend(tmp_path), frontend)

    assert exit_code == 2
    assert "run `uv run start.py` again" in capsys.readouterr().out
    install.assert_not_called()


def test_the_wait_retries_until_the_server_answers() -> None:
    """A refused connection while starting is tried again."""
    server = MagicMock(spec=subprocess.Popen)
    server.poll.return_value = None
    with (
        patch.object(
            start,
            "is_local_server_ready",
            side_effect=[URLError("starting"), True],
        ) as request,
        patch.object(start.time, "sleep") as sleep,
    ):
        start.wait_until_ready(server, start.BACKEND_READY_URL, "back end")

    assert request.call_count == 2
    sleep.assert_called_once_with(0.1)


def test_the_wait_fails_at_once_when_the_server_exits() -> None:
    """A server that stops is reported straight away instead of waited for."""
    server = MagicMock(spec=subprocess.Popen)
    server.poll.return_value = 1
    with pytest.raises(RuntimeError, match="back end stopped before it was ready"):
        start.wait_until_ready(server, start.BACKEND_READY_URL, "back end")


def test_the_wait_has_a_deadline() -> None:
    """A server that stays alive without answering can't block forever."""
    server = MagicMock(spec=subprocess.Popen)
    server.poll.return_value = None
    with (
        patch.object(start.time, "monotonic", side_effect=[0.0, 0.0, 31.0]),
        patch.object(start.time, "sleep"),
        patch.object(start, "is_local_server_ready", side_effect=URLError("starting")),
        pytest.raises(TimeoutError, match="did not become ready"),
    ):
        start.wait_until_ready(server, start.BACKEND_READY_URL, "back end")


def test_the_back_end_starts_first_and_the_ready_line_comes_last() -> None:
    """The API, then Vite once the API answers, then the ready line once Vite does."""
    events = MagicMock()
    backend = MagicMock(spec=subprocess.Popen)
    frontend = MagicMock(spec=subprocess.Popen)
    backend.poll.return_value = 0
    events.start.side_effect = [backend, frontend]
    with (
        patch.object(start, "start", events.start),
        patch.object(start, "wait_until_ready", events.ready),
        patch.object(start, "print", events.print, create=True),
        patch.object(start, "stop", events.stop),
        patch.object(start.signal, "signal"),
    ):
        exit_code: int = start.run_servers("http://localhost:5173", None)

    assert exit_code == 1
    assert events.mock_calls[:5] == [
        call.start(start.BACKEND_COMMAND, "backend"),
        call.ready(backend, start.BACKEND_READY_URL, "back end"),
        call.start(start.FRONTEND_COMMAND, "frontend"),
        call.ready(frontend, start.LOCAL_APP_URL, "front end"),
        call.print(start.ready_message("http://localhost:5173"), flush=True),
    ]
    assert events.mock_calls[-2:] == [call.stop(backend), call.stop(frontend)]


def test_a_server_that_stops_by_itself_is_named_with_its_exit_code() -> None:
    """The back end stopping stops the front end too, and says why."""
    backend = MagicMock(spec=subprocess.Popen)
    frontend = MagicMock(spec=subprocess.Popen)
    backend.poll.return_value = 3
    frontend.poll.return_value = None
    with (
        patch.object(start, "start", side_effect=[backend, frontend]),
        patch.object(start, "wait_until_ready"),
        patch.object(start, "print", create=True) as say,
        patch.object(start, "stop") as stop,
        patch.object(start.signal, "signal"),
    ):
        exit_code: int = start.run_servers("http://localhost:5173", None)

    assert exit_code == 1
    assert "The back end stopped (exit code 3)" in say.call_args.args[0]
    assert stop.mock_calls == [call(backend), call(frontend)]


def test_a_back_end_that_never_answers_is_stopped_and_vite_never_starts() -> None:
    """It says which server and what to do, with no traceback, and leaves nothing."""
    backend = MagicMock(spec=subprocess.Popen)
    with (
        patch.object(start, "start", return_value=backend) as start_server,
        patch.object(
            start,
            "wait_until_ready",
            side_effect=TimeoutError("The back end did not become ready."),
        ),
        patch.object(start, "print", create=True) as say,
        patch.object(start, "stop") as stop,
        patch.object(start.signal, "signal"),
    ):
        exit_code: int = start.run_servers("http://localhost:5173", None)

    assert exit_code == 1
    start_server.assert_called_once()
    assert "back end did not become ready" in say.call_args.args[0]
    assert "run `uv run start.py` again" in say.call_args.args[0]
    stop.assert_called_once_with(backend)


@pytest.mark.parametrize(
    "how_it_ends",
    [
        pytest.param(RuntimeError("The back end stopped."), id="a_server_failed"),
        pytest.param(KeyboardInterrupt(), id="ctrl_c"),
    ],
)
def test_ctrl_c_is_ignored_before_the_servers_are_stopped(
    how_it_ends: BaseException,
) -> None:
    """A failed start or Ctrl+C: Ctrl+C is ignored before any server is stopped."""
    events = MagicMock()
    backend = MagicMock(spec=subprocess.Popen)
    with (
        patch.object(start, "start", return_value=backend),
        patch.object(start, "wait_until_ready", side_effect=how_it_ends),
        patch.object(start, "print", create=True),
        patch.object(start, "stop", events.stop),
        patch.object(start.signal, "signal", events.signal),
    ):
        start.run_servers("http://localhost:5173", None)

    assert events.mock_calls[-2:] == [
        call.signal(signal.SIGINT, signal.SIG_IGN),
        call.stop(backend),
    ]


def test_ctrl_c_is_ignored_before_stopping_when_a_server_ends_by_itself() -> None:
    """After the ready line, the front end ends: both servers stop, Ctrl+C ignored."""
    events = MagicMock()
    backend = MagicMock(spec=subprocess.Popen)
    frontend = MagicMock(spec=subprocess.Popen)
    backend.poll.return_value = None
    frontend.poll.return_value = 1
    with (
        patch.object(start, "start", side_effect=[backend, frontend]),
        patch.object(start, "wait_until_ready"),
        patch.object(start, "print", create=True),
        patch.object(start, "stop", events.stop),
        patch.object(start.signal, "signal", events.signal),
    ):
        exit_code: int = start.run_servers("http://localhost:5173", None)

    assert exit_code == 1
    assert events.mock_calls[-3:] == [
        call.signal(signal.SIGINT, signal.SIG_IGN),
        call.stop(backend),
        call.stop(frontend),
    ]


def test_the_cloud_sync_warning_shows_again_under_the_ready_line() -> None:
    """The warning printed before the installs has scrolled away by then."""
    backend = MagicMock(spec=subprocess.Popen)
    backend.poll.return_value = 0
    with (
        patch.object(start, "start", return_value=backend),
        patch.object(start, "wait_until_ready"),
        patch.object(start, "print", create=True) as say,
        patch.object(start, "stop"),
        patch.object(start.signal, "signal"),
    ):
        start.run_servers("http://localhost:5173", "OneDrive")

    said: list[str] = [message.args[0] for message in say.call_args_list]
    ready_at: int = said.index(start.ready_message("http://localhost:5173"))
    assert said[ready_at + 1].startswith(start.install.cloud_sync_warning("OneDrive"))


def test_a_start_after_install_py_installs_nothing_more(tmp_path: Path) -> None:
    """`install.py` leaves the same fingerprint, so its reinstall isn't done twice."""
    frontend: Path = make_frontend(tmp_path)
    (frontend / "node_modules").mkdir()
    start.install.remember_frontend_install(frontend)

    assert not start.frontend_needs_install(frontend)


def test_ctrl_c_stops_both_servers_and_ends_quietly() -> None:
    """Ctrl+C while the app runs returns 0, with no traceback, and leaves nothing."""
    backend = MagicMock(spec=subprocess.Popen)
    frontend = MagicMock(spec=subprocess.Popen)
    backend.poll.return_value = None
    frontend.poll.return_value = None
    with (
        patch.object(start, "start", side_effect=[backend, frontend]),
        patch.object(start, "wait_until_ready"),
        patch.object(start, "print", create=True),
        patch.object(start.time, "sleep", side_effect=KeyboardInterrupt),
        patch.object(start, "stop") as stop,
        patch.object(start.signal, "signal"),
    ):
        exit_code: int = start.run_servers("http://localhost:5173", None)

    assert exit_code == 0
    assert stop.mock_calls == [call(backend), call(frontend)]


def test_only_the_first_ctrl_c_interrupts() -> None:
    """A second Ctrl+C (uv passes it on too) can't break into stopping the servers."""
    with patch.object(start.signal, "signal") as set_handler:
        start.stop_on_the_first_ctrl_c()

    (signal_number, on_ctrl_c) = set_handler.call_args.args
    assert signal_number == signal.SIGINT
    with pytest.raises(KeyboardInterrupt):
        on_ctrl_c(signal.SIGINT, None)
    on_ctrl_c(signal.SIGINT, None)


@pytest.mark.skipif(start.sys.platform == "win32", reason="process groups")
def test_stopping_signals_the_whole_group_even_after_its_leader_ended() -> None:
    """Npm or uv can end before what they started; the group is still stopped."""
    server = MagicMock(spec=subprocess.Popen)
    server.pid = 4321
    with patch.object(start.os, "killpg") as killpg:
        start.stop(server)

    killpg.assert_called_once_with(4321, signal.SIGTERM)
    server.wait.assert_called_once_with(timeout=start.STOP_WAIT_SECONDS)


@pytest.mark.skipif(start.sys.platform == "win32", reason="process groups")
def test_a_server_that_wont_stop_is_forced_after_the_wait() -> None:
    """A server still busy after the wait is killed, so start.py always ends."""
    server = MagicMock(spec=subprocess.Popen)
    server.pid = 4321
    server.wait.side_effect = [subprocess.TimeoutExpired("uvicorn", 10), 0]
    with patch.object(start.os, "killpg") as killpg:
        start.stop(server)

    assert killpg.mock_calls == [
        call(4321, signal.SIGTERM),
        call(4321, signal.SIGKILL),
    ]
    server.kill.assert_called_once()


@pytest.mark.skipif(start.sys.platform == "win32", reason="process groups")
def test_a_group_that_has_already_gone_is_not_an_error() -> None:
    """Stopping a server whose processes have all ended prints no traceback."""
    server = MagicMock(spec=subprocess.Popen)
    server.pid = 4321
    with patch.object(start.os, "killpg", side_effect=ProcessLookupError):
        start.stop(server)

    server.wait.assert_called_once()


def test_stopping_on_windows_ends_the_whole_tree() -> None:
    """`taskkill /T` runs even when npm or uv has ended before what it started."""
    server = MagicMock(spec=subprocess.Popen)
    server.pid = 4321
    server.poll.return_value = 0
    with (
        patch.object(start.sys, "platform", "win32"),
        patch.object(start.subprocess, "run") as run,
    ):
        start.stop(server)

    run.assert_called_once_with(
        ["taskkill", "/F", "/T", "/PID", "4321"],
        capture_output=True,
        check=False,
    )
    server.wait.assert_called_once_with(timeout=start.STOP_WAIT_SECONDS)


def test_a_failed_browser_install_warns_and_the_app_still_starts(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The app doesn't need the test browser; `install.py` can try it again later."""
    frontend: Path = make_frontend(tmp_path)

    def front_end_works_browser_fails(steps: list[object], rerun_command: str) -> int:
        """Stand in for the installs: npm works, the browser download doesn't."""
        (frontend / "node_modules").mkdir(exist_ok=True)
        return 0 if steps == [start.install.FRONTEND_INSTALL_STEP] else 1

    with (
        patch.object(
            start.subprocess,
            "run",
            return_value=subprocess.CompletedProcess([], 0),
        ),
        patch.object(
            start.install,
            "run_install_steps",
            side_effect=front_end_works_browser_fails,
        ),
    ):
        exit_code: int = start.install_what_changed(make_backend(tmp_path), frontend)

    assert exit_code == 0
    assert "starts anyway. Run `uv run install.py` later" in capsys.readouterr().out
    assert not start.frontend_needs_install(frontend)


def test_the_uvicorn_settings_differ_from_its_defaults_only_on_purpose() -> None:
    """Each change from uvicorn's own log settings is listed here (tasks 0029, 0028).

    Its status lines, such as "Uvicorn running on ...", are turned down to warnings;
    every line gets the time, level, message and where it came from; only failed
    requests print; and the app's own lines use the same format. A uvicorn upgrade that
    changes its defaults fails here.
    """
    settings_file: Path = start.BACKEND / "dev_logging.json"
    settings: dict[str, Any] = json.loads(settings_file.read_text(encoding="utf-8"))
    expected: dict[str, Any] = copy.deepcopy(uvicorn.config.LOGGING_CONFIG)
    expected["loggers"]["uvicorn.error"]["level"] = "WARNING"
    expected["filters"] = {
        "failed_requests_only": {
            "()": "risk_assessment.api.request_log.FailedRequestsOnly",
        },
    }
    expected["formatters"]["default"]["fmt"] = (
        "%(asctime)s %(levelprefix)s %(message)s  (%(name)s)"
    )
    expected["formatters"]["access"]["fmt"] = (
        "%(asctime)s %(levelprefix)s %(request_line)s %(status_code)s  (%(name)s)"
    )
    for formatter in expected["formatters"].values():
        formatter["datefmt"] = "%H:%M:%S"
    expected["handlers"]["access"]["filters"] = ["failed_requests_only"]
    expected["loggers"]["risk_assessment"] = {
        "handlers": ["default"],
        "level": "INFO",
        "propagate": False,
    }
    flag_at: int = start.BACKEND_COMMAND.index("--log-config")

    assert start.BACKEND_COMMAND[flag_at + 1] == settings_file.name
    assert settings == expected


def test_vite_prints_warnings_and_errors_but_not_its_address_box() -> None:
    """Vite's address box is info; `--logLevel warn` reaches Vite through npm's `--`."""
    assert start.FRONTEND_COMMAND[1:] == ["run", "dev", "--", "--logLevel", "warn"]


def test_the_back_end_runs_without_the_uvicorn_reloader() -> None:
    """Its reloader restarts with a Ctrl+C, which on Windows stopped the whole app."""
    assert "--reload" not in start.BACKEND_COMMAND


def test_the_code_stamp_changes_when_a_file_is_saved_added_or_removed(
    tmp_path: Path,
) -> None:
    """A save, a new file and a removed file change the stamp; other files don't."""
    module: Path = tmp_path / "app.py"
    module.write_text("ANSWER = 1\n")
    first: frozenset[tuple[str, int]] = start.code_stamp(tmp_path)
    (tmp_path / "notes.txt").write_text("not code")
    assert start.code_stamp(tmp_path) == first

    module.write_text("ANSWER = 2\n")
    os.utime(module, ns=(0, 1))
    saved: frozenset[tuple[str, int]] = start.code_stamp(tmp_path)
    assert saved != first

    (tmp_path / "package").mkdir()
    (tmp_path / "package" / "new.py").write_text("")
    added: frozenset[tuple[str, int]] = start.code_stamp(tmp_path)
    assert added != saved

    module.unlink()
    assert start.code_stamp(tmp_path) != added


def test_a_saved_back_end_file_restarts_only_the_back_end() -> None:
    """The old back end stops and a new one starts; the front end keeps running."""
    old_backend = MagicMock(spec=subprocess.Popen)
    new_backend = MagicMock(spec=subprocess.Popen)
    frontend = MagicMock(spec=subprocess.Popen)
    for server in (old_backend, new_backend, frontend):
        server.poll.return_value = None
    with (
        patch.object(start, "start", side_effect=[old_backend, frontend, new_backend]),
        patch.object(start, "wait_until_ready") as ready,
        patch.object(start, "code_stamp", side_effect=["before", "before", "after"]),
        patch.object(start, "print", create=True) as say,
        patch.object(start.time, "sleep", side_effect=[None, KeyboardInterrupt]),
        patch.object(start, "stop") as stop,
        patch.object(start.signal, "signal"),
    ):
        exit_code: int = start.run_servers("http://localhost:5173", None)

    assert exit_code == 0
    assert ready.call_args_list[-1].args[:3] == (
        new_backend,
        start.BACKEND_READY_URL,
        "back end",
    )
    assert call("The back end is running again.", flush=True) in say.mock_calls
    assert stop.mock_calls == [call(old_backend), call(new_backend), call(frontend)]


def test_a_change_that_breaks_the_back_end_waits_for_a_fix() -> None:
    """The error stays on screen, the app keeps going, and the next save restarts it."""
    old_backend = MagicMock(spec=subprocess.Popen)
    broken_backend = MagicMock(spec=subprocess.Popen)
    fixed_backend = MagicMock(spec=subprocess.Popen)
    frontend = MagicMock(spec=subprocess.Popen)
    for server in (old_backend, fixed_backend, frontend):
        server.poll.return_value = None
    broken_backend.poll.return_value = 1
    with (
        patch.object(
            start,
            "start",
            side_effect=[old_backend, frontend, broken_backend, fixed_backend],
        ),
        patch.object(
            start,
            "wait_until_ready",
            side_effect=[
                None,
                None,
                RuntimeError("The back end stopped before it was ready."),
                None,
            ],
        ),
        patch.object(
            start,
            "code_stamp",
            side_effect=["first", "first", "broken", "fixed"],
        ),
        patch.object(start, "print", create=True) as say,
        patch.object(start.time, "sleep", side_effect=[None, None, KeyboardInterrupt]),
        patch.object(start, "stop") as stop,
        patch.object(start.signal, "signal"),
    ):
        exit_code: int = start.run_servers("http://localhost:5173", None)

    assert exit_code == 0
    printed: str = "\n".join(str(each.args[0]) for each in say.call_args_list)
    assert "save a fix and the back end starts again" in printed
    assert "so the app was stopped" not in printed
    assert stop.mock_calls == [
        call(old_backend),
        call(broken_backend),
        call(fixed_backend),
        call(frontend),
    ]


def test_the_code_stamp_skips_a_file_removed_while_it_is_looked_at(
    tmp_path: Path,
) -> None:
    """A file listed and then removed before its time is read is left out, not fatal."""
    module: Path = tmp_path / "app.py"
    module.write_text("ANSWER = 1\n")
    removed: Path = tmp_path / "removed.py"
    with patch.object(start.Path, "rglob", return_value=iter([module, removed])):
        stamp: frozenset[tuple[str, int]] = start.code_stamp(tmp_path)

    assert stamp == frozenset({(str(module), module.stat().st_mtime_ns)})


def test_ctrl_c_while_the_back_end_restarts_stops_everything() -> None:
    """Ctrl+C during a restart returns 0 and stops the new back end and front end."""
    old_backend = MagicMock(spec=subprocess.Popen)
    new_backend = MagicMock(spec=subprocess.Popen)
    frontend = MagicMock(spec=subprocess.Popen)
    with (
        patch.object(start, "start", side_effect=[old_backend, frontend, new_backend]),
        patch.object(
            start,
            "wait_until_ready",
            side_effect=[None, None, KeyboardInterrupt],
        ),
        patch.object(start, "code_stamp", side_effect=["before", "after"]),
        patch.object(start, "print", create=True),
        patch.object(start, "stop") as stop,
        patch.object(start.signal, "signal"),
    ):
        exit_code: int = start.run_servers("http://localhost:5173", None)

    assert exit_code == 0
    assert stop.mock_calls == [call(old_backend), call(new_backend), call(frontend)]


def test_a_fixed_back_end_that_stops_by_itself_stops_the_app_again() -> None:
    """Once a save fixes the back end, it is watched again, as before the break."""
    old_backend = MagicMock(spec=subprocess.Popen)
    broken_backend = MagicMock(spec=subprocess.Popen)
    fixed_backend = MagicMock(spec=subprocess.Popen)
    frontend = MagicMock(spec=subprocess.Popen)
    for server in (old_backend, frontend):
        server.poll.return_value = None
    broken_backend.poll.return_value = 1
    fixed_backend.poll.return_value = 3
    with (
        patch.object(
            start,
            "start",
            side_effect=[old_backend, frontend, broken_backend, fixed_backend],
        ),
        patch.object(
            start,
            "wait_until_ready",
            side_effect=[
                None,
                None,
                RuntimeError("The back end stopped before it was ready."),
                None,
            ],
        ),
        patch.object(start, "code_stamp", side_effect=["first", "broken", "fixed"]),
        patch.object(start, "print", create=True) as say,
        patch.object(start.time, "sleep"),
        patch.object(start, "stop"),
        patch.object(start.signal, "signal"),
    ):
        exit_code: int = start.run_servers("http://localhost:5173", None)

    assert exit_code == 1
    assert "The back end stopped (exit code 3)" in say.call_args.args[0]
