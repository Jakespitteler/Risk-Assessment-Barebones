# /// script
# requires-python = ">=3.13"
# ///
"""Stop a Claude Code tool call that would touch a secret or break the repo's git rules.

Claude Code runs this before every tool call (a `PreToolUse` hook, set in
`.claude/settings.json`) and passes the call as JSON on standard input. Exit code 2
blocks the call, and what is printed to standard error is the reason Claude sees.
Exit code 0 leaves the decision to the normal permission rules.

The deny rules in `.claude/settings.json` only cover Claude's file tools and simple
commands such as `cat .env`. This hook reads the words of every shell command too, so
`python -c "print(open('.env').read())"` is caught as well.
"""

import json
import re
import shlex
import subprocess
import sys
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

PROTECTED_BRANCH: str = "main"

# A name that holds secrets or worker data. `.env.example` and `.env.sample` are
# templates with no real values, so they are allowed. The look-behinds and look-aheads
# only match whole names: `.venv`, `os.environ` and `monkey.keyboard` don't match.
SECRET_PATH_PATTERN: re.Pattern[str] = re.compile(
    r"""
    (?<![\w.])
    (
        \.env(?!\.(?:example|sample)(?![\w.-]))(?:\.[\w.-]+)?(?![\w-])
      | \.envrc(?![\w-])
      | [\w.-]+\.(?:pem|key)(?![\w-])      # private keys
      | secrets[/\\]                       # anything in a secrets folder
      | \.ssh[/\\]
      | backend[/\\]\.data(?![\w-])        # saved Take 5s: real workers' answers
    )
    """,
    re.VERBOSE,
)

SHELL_SEPARATOR_PATTERN: re.Pattern[str] = re.compile(r"&&|\|\||[;|\n]")
GIT_OPTIONS_WITH_A_VALUE: frozenset[str] = frozenset(
    {"-C", "-c", "--git-dir", "--work-tree"}
)
COMMIT_MESSAGE_OPTIONS: frozenset[str] = frozenset({"-m", "--message"})
FORCE_PUSH_OPTIONS: frozenset[str] = frozenset(
    {"-f", "--force", "--force-with-lease", "--force-if-includes"}
)
PATH_FIELDS: tuple[str, ...] = ("file_path", "path", "notebook_path")

type GitCommand = list[str]
"""A git command's words from the subcommand on, for example `["push", "origin"]`."""

type GitRule = Callable[[GitCommand, str], str | None]
"""A check on a git command and the current branch: why it is blocked, or None."""


def split_shell_command(command: str) -> list[list[str]]:
    """Split a command line into simple commands, each as a list of words.

    Args:
        command: The full command line. It may chain commands with `&&`, `||`, `;`
            or `|`.

    Returns:
        One list of words per simple command, with quotes removed as a shell would.
    """
    simple_commands: list[list[str]] = []
    for part in SHELL_SEPARATOR_PATTERN.split(command):
        try:
            words: list[str] = shlex.split(part)
        except ValueError:  # an unclosed quote: fall back to plain spaces
            words = part.split()
        if words:
            simple_commands.append(words)
    return simple_commands


def without_commit_messages(words: list[str]) -> list[str]:
    """Drop the text after `-m` or `--message`, so a message may mention `.env`.

    Args:
        words: One git command's words.

    Returns:
        The same words without any commit message.
    """
    kept_words: list[str] = []
    skip_next_word: bool = False
    for word in words:
        if skip_next_word:
            skip_next_word = False
        elif word in COMMIT_MESSAGE_OPTIONS:
            skip_next_word = True
        elif not word.startswith("--message="):
            kept_words.append(word)
    return kept_words


def secret_named_in(text: str) -> str | None:
    """Find the first secret or worker-data path named in some text.

    Args:
        text: A file path or one word of a shell command.

    Returns:
        The name that matched, or None when the text names no secret.
    """
    match: re.Match[str] | None = SECRET_PATH_PATTERN.search(text)
    return match.group(0) if match else None


def secret_reason(secret: str) -> str:
    """Say why a call that names a secret is blocked.

    Args:
        secret: The secret or worker-data name that was found.

    Returns:
        The reason Claude is shown.
    """
    return f"{secret} may hold secrets or worker data. Agents never read or change it."


def git_command_in(words: list[str]) -> GitCommand | None:
    """Pick out the git subcommand and its arguments from one simple command.

    Args:
        words: One simple command's words, such as `["git", "-C", "repo", "push"]`.

    Returns:
        The words from the subcommand on (`["push"]`), or None when this is not git.
    """
    if not words or Path(words[0]).stem != "git":
        return None
    position: int = 1
    while position < len(words) and words[position].startswith("-"):
        position += 2 if words[position] in GIT_OPTIONS_WITH_A_VALUE else 1
    return words[position:] or None


def block_no_verify(git_command: GitCommand, current_branch: str) -> str | None:
    """Block skipping git's own checks."""
    if "--no-verify" in git_command:
        return "--no-verify skips the repo's checks. Fix what the check reports."
    return None


def block_force_push(git_command: GitCommand, current_branch: str) -> str | None:
    """Block a push that could overwrite commits already on GitHub."""
    if git_command[0] == "push" and FORCE_PUSH_OPTIONS.intersection(git_command):
        return "A force push can throw away commits. Ask the human to do it."
    return None


def block_push_to_main(git_command: GitCommand, current_branch: str) -> str | None:
    """Block a push to `main`, such as `git push origin main` or `HEAD:main`."""
    main_names: tuple[str, ...] = (PROTECTED_BRANCH, f"refs/heads/{PROTECTED_BRANCH}")
    targets_main: bool = any(
        word.split(":")[-1] in main_names for word in git_command[1:]
    )
    if git_command[0] == "push" and targets_main:
        return f"Never push to {PROTECTED_BRANCH}. Push the task branch (AGENTS.md)."
    return None


def block_work_on_main(git_command: GitCommand, current_branch: str) -> str | None:
    """Block a commit or push made while `main` is checked out."""
    if git_command[0] in ("commit", "push") and current_branch == PROTECTED_BRANCH:
        return f"You are on {PROTECTED_BRANCH}. Create the task branch (AGENTS.md)."
    return None


GIT_RULES: tuple[GitRule, ...] = (
    block_no_verify,
    block_force_push,
    block_push_to_main,
    block_work_on_main,
)


def reason_to_block_command(command: str, current_branch: str) -> str | None:
    """Decide whether a shell command must be blocked.

    Args:
        command: The full command line Claude wants to run.
        current_branch: The branch checked out where the command runs, or "".

    Returns:
        Why the command is blocked, or None when it may run.
    """
    for words in split_shell_command(command):
        git_command: GitCommand | None = git_command_in(words)
        words_to_scan: list[str] = (
            without_commit_messages(words) if git_command else words
        )
        for word in words_to_scan:
            if secret := secret_named_in(word):
                return secret_reason(secret)
        if git_command is None:
            continue
        for rule in GIT_RULES:
            if reason := rule(git_command, current_branch):
                return reason
    return None


def reason_to_block_tool_call(
    tool_name: str, tool_input: Mapping[str, Any], current_branch: str
) -> str | None:
    """Decide whether a tool call must be blocked.

    Args:
        tool_name: The tool Claude wants to use, such as `Bash`, `Read` or `Edit`.
        tool_input: The tool's arguments, as Claude Code sends them.
        current_branch: The branch checked out where Claude is working, or "".

    Returns:
        Why the call is blocked, or None when it may go ahead.
    """
    for field in PATH_FIELDS:
        path: object = tool_input.get(field)
        if isinstance(path, str) and (secret := secret_named_in(path)):
            return secret_reason(secret)
    command: object = tool_input.get("command")
    if tool_name == "Bash" and isinstance(command, str):
        return reason_to_block_command(command, current_branch)
    return None


def current_branch_in(folder: str) -> str:
    """Ask git which branch is checked out.

    Args:
        folder: The folder Claude is working in, or "" for the current folder.

    Returns:
        The branch name, or "" when the folder is not in a git repository.
    """
    result: subprocess.CompletedProcess[str] = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=folder or None,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip()


def main() -> int:
    """Read the tool call from standard input and block it if a rule says so.

    Returns:
        2 to block the call, otherwise 0.
    """
    hook_input: dict[str, Any] = json.load(sys.stdin)
    tool_input: dict[str, Any] = hook_input.get("tool_input") or {}
    current_branch: str = current_branch_in(hook_input.get("cwd", ""))
    reason: str | None = reason_to_block_tool_call(
        hook_input.get("tool_name", ""), tool_input, current_branch
    )
    if reason is None:
        return 0
    print(
        f"Blocked by scripts/claude_hooks/guard_tool_use.py: {reason}", file=sys.stderr
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
