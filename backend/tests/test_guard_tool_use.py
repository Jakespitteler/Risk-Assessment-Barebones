"""Tests for the hook that stops Claude Code touching secrets or breaking git rules."""

import pytest
from scripts.claude_hooks.guard_tool_use import (
    reason_to_block_command,
    reason_to_block_tool_call,
)

TASK_BRANCH: str = "claude/0011-agent-safety"


@pytest.mark.parametrize(
    "command",
    [
        "cat .env",
        "cat backend/.env.local",
        "cat 'backend\\.env'",
        "python -c \"print(open('.env').read())\"",
        "grep KEY .envrc",
        "cp deploy.pem /tmp",
        "ls secrets/",
        "cat ~/.ssh/id_ed25519",
        "sqlite3 backend/.data/take5.sqlite3 'select * from take5s'",
        "git status && cat .env",
        "echo hi | tee .env",
    ],
)
def test_a_command_that_names_a_secret_is_blocked(command: str) -> None:
    """Secrets and saved Take 5s are blocked however the command reaches them."""
    reason: str | None = reason_to_block_command(command, TASK_BRANCH)

    assert reason is not None
    assert "secrets or worker data" in reason


@pytest.mark.parametrize(
    "command",
    [
        "uv sync --locked",
        "ls backend/.venv",
        "cat .env.example",
        "diff .env.example .env.sample",
        "grep -rn os.environ backend/src",
        "python -m pytest tests/test_settings.py",
        "cat docs/keyboard.md",
        'git commit -m "Deny reading .env files"',
        "git commit --message='Never read .env'",
    ],
)
def test_a_command_that_only_looks_like_a_secret_may_run(command: str) -> None:
    """Names that merely contain `env`, templates, and commit messages are allowed."""
    assert reason_to_block_command(command, TASK_BRANCH) is None


@pytest.mark.parametrize(
    "command",
    [
        "git push origin main",
        "git push origin HEAD:main",
        "git push origin claude/0011:refs/heads/main",
        "git -C ../repo push origin main",
        "git push --force origin claude/0011",
        "git push -f",
        "git push --force-with-lease origin claude/0011",
        "git commit --no-verify -m 'Skip the checks'",
        "git add . && git push origin main",
    ],
)
def test_a_risky_git_command_is_blocked(command: str) -> None:
    """Pushes to main, force pushes and skipped checks are blocked on any branch."""
    assert reason_to_block_command(command, TASK_BRANCH) is not None


@pytest.mark.parametrize("command", ["git commit -m 'Tidy'", "git push"])
def test_committing_or_pushing_while_on_main_is_blocked(command: str) -> None:
    """With main checked out, even a plain commit or push is blocked."""
    reason: str | None = reason_to_block_command(command, "main")

    assert reason is not None
    assert "task branch" in reason


@pytest.mark.parametrize(
    "command",
    [
        "git push -u origin claude/0011-agent-safety",
        "git commit -m 'Add the guard hook'",
        "git log --oneline main",
        "git diff main...HEAD",
        "git checkout main",
    ],
)
def test_normal_work_on_a_task_branch_may_run(command: str) -> None:
    """Committing, pushing the task branch and reading main are all allowed."""
    assert reason_to_block_command(command, TASK_BRANCH) is None


@pytest.mark.parametrize(
    ("tool_name", "tool_input"),
    [
        ("Read", {"file_path": "/repo/backend/.env"}),
        ("Edit", {"file_path": "C:\\repo\\.env.production"}),
        ("Grep", {"pattern": "KEY", "path": "secrets/"}),
        ("Bash", {"command": "cat .env"}),
    ],
)
def test_a_tool_call_that_names_a_secret_is_blocked(
    tool_name: str, tool_input: dict[str, str]
) -> None:
    """The file tools are checked by path, and shell commands by their words."""
    assert reason_to_block_tool_call(tool_name, tool_input, TASK_BRANCH) is not None


def test_an_ordinary_tool_call_may_go_ahead() -> None:
    """Reading a source file is allowed."""
    tool_input: dict[str, str] = {"file_path": "/repo/backend/src/settings.py"}

    assert reason_to_block_tool_call("Read", tool_input, TASK_BRANCH) is None
