"""Regression tests for preparing and starting the two development servers."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, call, patch
from urllib.error import URLError

import pytest

from scripts import dev


@pytest.mark.parametrize("partial_install", [False, True])
def test_missing_vite_installs_packages(tmp_path: Path, partial_install: bool) -> None:
    """An absent or incomplete node_modules folder must not skip installation."""
    if partial_install:
        (tmp_path / "frontend" / "node_modules").mkdir(parents=True)
    with (
        patch.object(dev, "REPO_ROOT", tmp_path),
        patch.object(dev.subprocess, "run") as install,
    ):
        dev.install_frontend_if_needed()

    install.assert_called_once_with(
        [dev.NPM, "ci"],
        cwd=tmp_path / "frontend",
        env=dev.SERVER_ENVIRONMENT,
        check=True,
    )


@pytest.mark.parametrize("platform", ["win32", "linux"])
def test_installed_vite_needs_no_install(tmp_path: Path, platform: str) -> None:
    """A working Vite installation is reused on Windows and Linux."""
    node_modules: Path = tmp_path / "frontend" / "node_modules"
    executable: str = "vite.cmd" if platform == "win32" else "vite"
    for relative_path in (Path(".bin") / executable, Path("vite/bin/vite.js")):
        target: Path = node_modules / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.touch()
    with (
        patch.object(dev, "REPO_ROOT", tmp_path),
        patch.object(dev.sys, "platform", platform),
        patch.object(dev.subprocess, "run") as install,
    ):
        dev.install_frontend_if_needed()

    install.assert_not_called()


def test_backend_wait_retries_until_the_api_responds() -> None:
    """A refused connection during startup is retried before Vite is started."""
    server: MagicMock = MagicMock(spec=subprocess.Popen)
    server.poll.return_value = None
    response: MagicMock = MagicMock()
    response.__enter__.return_value.status = 200
    with (
        patch.object(
            dev, "urlopen", side_effect=[URLError("starting"), response]
        ) as request,
        patch.object(dev.time, "sleep") as sleep,
    ):
        dev.wait_for_backend(server)

    assert request.call_count == 2
    sleep.assert_called_once_with(0.1)


def test_backend_wait_fails_when_the_server_exits() -> None:
    """An API process that exits is reported immediately instead of waiting."""
    server: MagicMock = MagicMock(spec=subprocess.Popen)
    server.poll.return_value = 1
    with pytest.raises(RuntimeError, match="stopped before its API was ready"):
        dev.wait_for_backend(server)


def test_backend_wait_has_a_deadline() -> None:
    """A backend that stays alive without responding cannot block forever."""
    server: MagicMock = MagicMock(spec=subprocess.Popen)
    server.poll.return_value = None
    with (
        patch.object(dev.time, "monotonic", side_effect=[0.0, 0.0, 31.0]),
        patch.object(dev.time, "sleep"),
        patch.object(dev, "urlopen", side_effect=URLError("starting")),
        pytest.raises(TimeoutError, match="did not become ready"),
    ):
        dev.wait_for_backend(server)


def test_servers_start_only_after_install_and_api_readiness() -> None:
    """Preparation finishes first, then the API is ready before Vite can start."""
    events: MagicMock = MagicMock()
    backend: MagicMock = MagicMock(spec=subprocess.Popen)
    frontend: MagicMock = MagicMock(spec=subprocess.Popen)
    backend.poll.return_value = 0
    events.start.side_effect = [backend, frontend]
    with (
        patch.object(dev.subprocess, "run", events.sync),
        patch.object(dev, "install_frontend_if_needed", events.install),
        patch.object(dev, "start", events.start),
        patch.object(dev, "wait_for_backend", events.ready),
        patch.object(dev, "stop", events.stop),
    ):
        dev.run_both()

    assert events.mock_calls == [
        call.sync(
            ["uv", "sync", "--locked"],
            cwd=dev.REPO_ROOT / "backend",
            env=dev.SERVER_ENVIRONMENT,
            check=True,
        ),
        call.install(),
        call.start(dev.BACKEND_COMMAND, "backend"),
        call.ready(backend),
        call.start(dev.FRONTEND_COMMAND, "frontend"),
        call.stop(backend),
        call.stop(frontend),
    ]


def test_failed_backend_readiness_stops_it_without_starting_vite() -> None:
    """An unsuccessful startup leaves no backend process behind."""
    backend: MagicMock = MagicMock(spec=subprocess.Popen)
    with (
        patch.object(dev.subprocess, "run"),
        patch.object(dev, "install_frontend_if_needed"),
        patch.object(dev, "start", return_value=backend) as start,
        patch.object(dev, "wait_for_backend", side_effect=TimeoutError("not ready")),
        patch.object(dev, "stop") as stop,
        pytest.raises(TimeoutError, match="not ready"),
    ):
        dev.run_both()

    start.assert_called_once_with(dev.BACKEND_COMMAND, "backend")
    stop.assert_called_once_with(backend)
