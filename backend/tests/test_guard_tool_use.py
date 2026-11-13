"""Tests for the hook that stops Claude Code touching secrets or breaking git rules."""

import io
import json
from pathlib import Path

import pytest
from scripts.claude_hooks import guard_tool_use
from scripts.claude_hooks.guard_tool_use import (
    current_branch_in,
    reason_to_block_command,
    reason_to_block_tool_call,
)

TASK_BRANCH: str = "claude/0011-agent-safety"


@pytest.mark.parametrize(
    "command",
    [
        "cat .env",
        "cat backend/.env.local",
        "cat .ENV",
        "Get-Content backend\\.env",
        "type secrets\\prod.txt",
        "python -c \"print(open('.env').read())\"",
        "node -e \"require('fs').readFileSync('.env.production')\"",
        "grep KEY .envrc",
        "cp deploy.pem /tmp",
        "cat ~/.ssh/id_ed25519",
        "ls ~/.ssh",
        "cd secrets",
        "cat ~/.aws/credentials",
        "cat ~/.netrc",
        "sqlite3 backend/.data/take5.sqlite3 .dump",
        "cd backend && sqlite3 .data/take5.sqlite3 .dump",
        "ls backend//.data",
        "git status && cat .env",
        "echo hi | tee .env",
        "echo hi>.env",
        "git add -f .env",
    ],
)
def test_a_command_that_names_a_secret_is_blocked(command: str) -> None:
    """Secrets and saved Take 5s are blocked however the command names them."""
    reason: str | None = reason_to_block_command(command, TASK_BRANCH)

    assert reason is not None
    assert "secrets or worker data" in reason


@pytest.mark.parametrize(
    "command",
    [
        "uv sync --locked",
        "ls backend/.venv",
        "grep -rn os.environ backend/src",
        "grep -rn process.env frontend/src",
        "grep -rn event.key frontend/src",
        "jq .data.items reply.json",
        "python -m pytest tests/test_settings.py",
        "cat docs/keyboard.md",
        'echo "no secrets here"',
        'git commit -m "Deny reading .env files"',
        "git commit --message='Never read .env'",
        "git commit -am 'Ignore .env and backend/.data'",
        'git commit -m "Guard: block .env; block keys"',
        "git commit -m \"$(cat <<'EOF'\nBlock .env\n\ngit push --force\nEOF\n)\"",
        'gh pr create --title "Guard .env" --body "Denies .env and backend/.data"',
    ],
)
def test_a_command_that_only_mentions_a_secret_may_run(command: str) -> None:
    """Names that only contain `env` or `key`, and commit or PR text, are allowed."""
    assert reason_to_block_command(command, TASK_BRANCH) is None


@pytest.mark.parametrize(
    "command",
    [
        "git push origin main",
        "git push origin HEAD:main",
        "git push origin claude/0011:refs/heads/main",
        "git push origin :main",
        "git push --all",
        "git -C ../repo push origin main",
        "FOO=1 git push origin main",
        "sudo git push origin main",
        "(git push origin main)",
        "echo hi & git push origin main",
        '& "C:\\Program Files\\Git\\bin\\git.exe" push origin main',
        "git push --force origin claude/0011",
        "git push -f",
        "git push -fu origin claude/0011",
        "git push --force-with-lease=claude/0011 origin claude/0011",
        "git push --forc origin claude/0011",
        "git push origin +claude/0011",
        "git push --mirror",
        "git commit --no-verify -m 'Skip the checks'",
        "git commit --no-verif -m 'Skip the checks'",
        "git commit -n -m 'Skip the checks'",
        "HUSKY=0 git commit -nm 'Skip the checks'",
        "git checkout main && git commit -m x",
        "git switch main; git merge claude/0011",
        "gh pr merge 13 --squash",
    ],
)
def test_a_risky_git_command_is_blocked(command: str) -> None:
    """Pushes to main, force pushes, skipped checks and merges are blocked."""
    assert reason_to_block_command(command, TASK_BRANCH) is not None


@pytest.mark.parametrize(
    "command",
    ["git commit -m 'Tidy'", "git push", "git merge claude/0011", "git revert HEAD"],
)
def test_changing_main_while_it_is_checked_out_is_blocked(command: str) -> None:
    """With main checked out, even a plain commit, merge or push is blocked."""
    reason: str | None = reason_to_block_command(command, "main")

    assert reason is not None
    assert "task branch" in reason


@pytest.mark.parametrize(
    "command",
    [
        "git push -u origin claude/0011-agent-safety",
        "git push --follow-tags origin claude/0011-agent-safety",
        "git commit -m 'Add the guard hook'",
        "git log --oneline main",
        "git diff main...HEAD",
        "git fetch origin main",
        "git rebase origin/main",
        "git checkout -b claude/0012 main && git commit -m x",
        "git checkout main -- docs/spec.md && git commit -m x",
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
        ("Write", {"file_path": "/repo/backend/.data/take5.sqlite3"}),
        ("NotebookEdit", {"notebook_path": "/repo/secrets/notes.ipynb"}),
        ("Grep", {"pattern": "KEY", "path": "secrets/"}),
        ("Grep", {"pattern": "KEY", "glob": "**/.env"}),
        ("Glob", {"pattern": "**/.env*"}),
        ("Bash", {"command": "cat .env"}),
        ("PowerShell", {"command": "Get-Content .env"}),
    ],
)
def test_a_tool_call_that_names_a_secret_is_blocked(
    tool_name: str, tool_input: dict[str, str]
) -> None:
    """File tools are checked by path, and Bash and PowerShell by their words."""
    assert reason_to_block_tool_call(tool_name, tool_input, TASK_BRANCH) is not None


@pytest.mark.parametrize(
    ("tool_name", "tool_input"),
    [
        ("Read", {"file_path": "/repo/backend/src/settings.py"}),
        ("Grep", {"pattern": "\\.env", "path": "docs"}),
    ],
)
def test_an_ordinary_tool_call_may_go_ahead(
    tool_name: str, tool_input: dict[str, str]
) -> None:
    """Reading code, or searching the docs for the word `.env`, is allowed."""
    assert reason_to_block_tool_call(tool_name, tool_input, TASK_BRANCH) is None


def run_guard(monkeypatch: pytest.MonkeyPatch, hook_input: dict[str, object]) -> int:
    """Run the hook's `main` with a tool call on standard input, as Claude Code does."""
    stdin_bytes: bytes = json.dumps(hook_input, ensure_ascii=False).encode()
    monkeypatch.setattr("sys.stdin", io.TextIOWrapper(io.BytesIO(stdin_bytes)))
    return guard_tool_use.main()


def test_main_blocks_with_exit_code_2_and_says_why(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Claude Code blocks a call on exit code 2 and shows Claude standard error."""
    hook_input: dict[str, object] = {
        "tool_name": "Read",
        "tool_input": {"file_path": "/repo/.env"},
    }

    assert run_guard(monkeypatch, hook_input) == 2
    assert ".env may hold secrets" in capsys.readouterr().err


def test_main_allows_a_safe_call_with_text_that_is_not_ascii(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Claude Code sends UTF-8, which is read right whatever the code page."""
    hook_input: dict[str, object] = {
        "tool_name": "Bash",
        "tool_input": {"command": "git commit -m 'Don’t start yet – fixed'"},
        "cwd": str(tmp_path),
    }

    assert run_guard(monkeypatch, hook_input) == 0


def test_the_branch_is_unknown_outside_a_repository_or_folder(tmp_path: Path) -> None:
    """No repository, or a folder that is gone, gives no branch rather than an error."""
    assert current_branch_in(str(tmp_path)) == ""
    assert current_branch_in(str(tmp_path / "missing")) == ""
