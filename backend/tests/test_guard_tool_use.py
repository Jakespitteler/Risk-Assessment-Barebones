"""Tests for the hook that stops Claude Code touching secrets or breaking git rules."""

import io
import json
import subprocess
import sys
from pathlib import Path

import pytest
from scripts.claude_hooks import guard_tool_use
from scripts.claude_hooks.guard_tool_use import (
    current_branch_in,
    reason_to_block_command,
    reason_to_block_tool_call,
)

TASK_BRANCH: str = "claude/0011-agent-safety"
HEREDOC_COMMIT: str = 'git commit -m "$(cat <<\'EOF\'\nFix the "quoted" case\nEOF\n)"'


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
        "cat ~/.netrc ~/.git-credentials",
        "cp deploy.pem cert.p12 cert.pfx /tmp",
        "cat ~/.ssh/id_ed25519",
        "cat id_rsa",
        "ls ~/.ssh",
        "cat ~/.aws/credentials",
        "ls secrets/",
        "sqlite3 backend/.data/take5.sqlite3 .dump",
        "cd backend && sqlite3 .data/take5.sqlite3 .dump",
        "ls backend//.data",
        "git status && cat .env",
        "echo hi | tee .env",
        "echo hi>.env",
        "git add -f .env",
        "git commit -F .env",
        'git commit -m "$(cat .env)"',
        "gh pr create --title x --body-file .env",
        "gh pr comment 13 --body-file backend/.data/take5.sqlite3",
        f"{HEREDOC_COMMIT}; cat .env",
    ],
)
def test_a_command_that_names_a_secret_is_blocked(command: str) -> None:
    """Secrets and saved Take 5s are blocked however the command names them."""
    reason: str | None = reason_to_block_command(command, TASK_BRANCH)

    assert reason is not None
    assert "secrets or worker data" in reason


def test_a_message_that_names_a_secret_is_blocked_with_a_way_round() -> None:
    """Message text is not trusted either; the reason says to pass a file instead."""
    reason: str | None = reason_to_block_command("git commit -m 'Deny .env'", "")

    assert reason is not None
    assert "write it to a file" in reason


@pytest.mark.parametrize(
    "command",
    [
        "uv sync --locked",
        "ls backend/.venv",
        "grep -rn os.environ backend/src",
        "grep -rn process.env frontend/src",
        "grep -rn event.key frontend/src",
        "grep -rn secrets docs/",
        "uv run pytest -k secrets",
        "python -c 'import secrets'",
        "jq .data reply.json",
        "git status --short | grep -v .data",
        "python -m pytest tests/test_settings.py",
        "cat docs/keyboard.md",
        "git commit -F commit-message.txt",
        "gh pr create --title 'Agent safety' --body-file pr-body.md",
        HEREDOC_COMMIT,
        'gh pr create --title T --body "Jake said \\"go\\". | a | b |"',
    ],
)
def test_a_command_that_only_looks_like_a_secret_may_run(command: str) -> None:
    """Names that only contain `env`, `key`, `secrets` or `.data` are allowed."""
    assert reason_to_block_command(command, TASK_BRANCH) is None


@pytest.mark.parametrize(
    "command",
    [
        "git push origin main",
        "git push origin HEAD:main",
        "git push origin HEAD:heads/main",
        "git push origin claude/0011:refs/heads/main",
        "git push origin :main",
        "git push --all",
        "git push --branches",
        "git -C ../repo push origin main",
        "FOO=1 git push origin main",
        "sudo git push origin main",
        "env -i git push origin main",
        "xargs git push origin main",
        "(git push origin main)",
        "{ git push origin main; }",
        "if true; then git push origin main; fi",
        "echo `git push origin main`",
        "echo hi & git push origin main",
        f"{HEREDOC_COMMIT}\ngit push origin main",
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
        "HUSKY=0 git commit -anm 'Skip the checks'",
        "git checkout main && git commit -m x",
        "git switch main; git merge claude/0011",
        "gh pr merge 13 --squash",
        "gh -R owner/repo pr merge 13",
        "gh api -X PUT repos/owner/repo/pulls/13/merge",
        "git push \\\n  --force origin claude/0011",
        "git commit -m x \\\n  --no-verify",
        "git push origin \\\n  main",
        "# don't forget\ngit push origin main\necho 'done'",
        'Set-Location "C:\\repo\\"; git push origin main; Write-Host "done"',
        'echo "$(git push origin main)"',
        'out="$(git push --force origin claude/0011 2>&1)"',
        "if git push origin main; then echo ok; fi",
        "while ! git push origin main; do sleep 1; done",
        "timeout 60 git push origin main",
        "sudo -u jake git push origin main",
        "git push origin main>/dev/null",
    ],
)
def test_a_risky_git_command_is_blocked(command: str) -> None:
    """Pushes to main, force pushes, skipped checks and merges are blocked."""
    assert reason_to_block_command(command, TASK_BRANCH) is not None


@pytest.mark.parametrize(
    "command",
    [
        "git commit -m 'Tidy'",
        "git push",
        "git merge claude/0011",
        "git revert HEAD",
        "git cherry-pick abc123",
        "git am fix.patch",
        "git rebase claude/0011",
        "git checkout . && git commit -m x",
        "git checkout docs/spec.md && git commit -am x",
        "cat > m.txt <<EOF\nDon't start yet\nEOF\ngit commit -F m.txt && echo 'ok'",
    ],
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
        "git commit -m x -uno",
        "git commit --message='Block -n on commit'",
        'git commit -m "Explain \\"force\\"; git push origin main is blocked"',
        "git log --oneline main",
        "git diff main...HEAD",
        "git fetch origin main",
        "git rebase origin/main",
        "git checkout -b claude/0012 main && git commit -m x",
        "git checkout main docs/spec.md && git commit -m x",
        "git checkout main -- docs/spec.md && git commit -m x",
        "gh pr create --title 'Merge the guard' --body-file pr-body.md",
        "gh pr list --search merge",
        "grep -rn '\\.data' frontend/src",
    ],
)
def test_normal_work_on_a_task_branch_may_run(command: str) -> None:
    """Committing, pushing the task branch, reading main and opening a PR may run."""
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
        ("mcp__github__merge_pull_request", {"pullNumber": "13"}),
    ],
)
def test_a_risky_tool_call_is_blocked(
    tool_name: str, tool_input: dict[str, str]
) -> None:
    """File tools are checked by path, shells by their text, and merging by name."""
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


def run_guard(
    monkeypatch: pytest.MonkeyPatch, hook_input: dict[str, object], encoding: str
) -> int:
    """Run the hook's `main` with a tool call on standard input, as Claude Code does.

    Args:
        monkeypatch: Replaces standard input for the test.
        hook_input: The tool call, sent as UTF-8 as Claude Code sends it.
        encoding: The code page Python would use to read standard input as text.

    Returns:
        The hook's exit code.
    """
    stdin_bytes: bytes = json.dumps(hook_input, ensure_ascii=False).encode()
    stdin = io.TextIOWrapper(io.BytesIO(stdin_bytes), encoding=encoding)
    monkeypatch.setattr("sys.stdin", stdin)
    return guard_tool_use.main()


def test_main_blocks_with_exit_code_2_and_says_why(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Claude Code blocks a call on exit code 2 and shows Claude standard error."""
    hook_input: dict[str, object] = {
        "tool_name": "Read",
        "tool_input": {"file_path": "/repo/.env"},
    }

    assert run_guard(monkeypatch, hook_input, "utf-8") == 2
    assert ".env may hold secrets" in capsys.readouterr().err


def test_main_reads_utf_8_even_on_a_windows_code_page(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A curly quote in UTF-8 can't be read as cp1252 text, so the hook reads bytes."""
    hook_input: dict[str, object] = {
        "tool_name": "Bash",
        "tool_input": {"command": "git commit -m '”Don’t start yet” fixed'"},
        "cwd": str(tmp_path),
    }

    assert run_guard(monkeypatch, hook_input, "cp1252") == 0


def test_a_broken_guard_blocks_the_call() -> None:
    """Input the guard can't read fails closed, with exit code 2 and the error."""
    guard_script: Path = Path(guard_tool_use.__file__)

    result: subprocess.CompletedProcess[str] = subprocess.run(
        [sys.executable, str(guard_script)],
        input="not json",
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert "so the call is blocked" in result.stderr


def test_the_branch_is_unknown_outside_a_repository_or_folder(tmp_path: Path) -> None:
    """No repository, or a folder that is gone, gives no branch rather than an error."""
    assert current_branch_in(str(tmp_path)) == ""
    assert current_branch_in(str(tmp_path / "missing")) == ""


def test_a_new_branch_from_main_may_be_committed_to() -> None:
    """`git checkout -b` names a branch, even one with a dot in it."""
    command: str = "git checkout -b claude/0012-v1.2 && git commit -m x"

    assert reason_to_block_command(command, "main") is None
