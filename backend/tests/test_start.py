"""Tests for `start.py`: checking, installing what changed, and starting both halves."""

import copy
import json
import signal
import socket
import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, call, patch
from urllib.error import URLError

import pytest
import start
import uvicorn.config


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


def test_the_uvicorn_settings_turn_down_only_its_status_lines() -> None:
    """Uvicorn's "running on" line is `uvicorn.error` info; requests still show.

    The file is uvicorn's own default log settings, from the installed uvicorn, with
    that one logger at warnings, so its errors, reload notices and tracebacks still
    reach the terminal. A uvicorn upgrade that changes its defaults fails here.
    """
    settings_file: Path = start.BACKEND / "dev_logging.json"
    settings: dict[str, Any] = json.loads(settings_file.read_text(encoding="utf-8"))
    expected: dict[str, Any] = copy.deepcopy(uvicorn.config.LOGGING_CONFIG)
    expected["loggers"]["uvicorn.error"]["level"] = "WARNING"
    flag_at: int = start.BACKEND_COMMAND.index("--log-config")

    assert start.BACKEND_COMMAND[flag_at + 1] == settings_file.name
    assert settings == expected


def test_vite_prints_warnings_and_errors_but_not_its_address_box() -> None:
    """Vite's address box is info; `--logLevel warn` reaches Vite through npm's `--`."""
    assert start.FRONTEND_COMMAND[1:] == ["run", "dev", "--", "--logLevel", "warn"]
