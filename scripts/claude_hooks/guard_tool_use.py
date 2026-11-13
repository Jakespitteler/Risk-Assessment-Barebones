# /// script
# requires-python = ">=3.13"
# ///
"""Stop a Claude Code tool call that would touch a secret or break the repo's git rules.

Claude Code runs this before each file tool and shell command (a `PreToolUse` hook,
set in `.claude/settings.json`) and passes the call as JSON on standard input. Exit
code 2 blocks the call, and what is printed to standard error is the reason Claude
sees. Exit code 0 leaves the decision to the normal permission rules.

The deny rules in `.claude/settings.json` only cover Claude's file tools and simple
commands such as `cat .env`. This hook reads every word of a shell command too, so
`python -c "print(open('.env').read())"` is caught as well. It is a soft guard: it
matches words, so a command that reads a file without naming it (`grep -r KEY .`) or
a script that opens one gets past it. `docs/decisions.md` lists the limits.
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
SHELL_TOOLS: frozenset[str] = frozenset({"Bash", "PowerShell"})
PATH_FIELDS: tuple[str, ...] = ("file_path", "path", "notebook_path", "glob")

# A name that holds secrets or worker data. The look-behind and look-aheads only match
# whole names, so `.venv`, `os.environ` and `process.env.PORT` don't match. Key files
# ending in `.key` are left to the deny rules, because `event.key` is ordinary code.
SECRET_PATH_PATTERN: re.Pattern[str] = re.compile(
    r"""
    (?<![\w.-])
    (
        \.env(?:\.[\w.-]+)?(?![\w-])           # .env, .env.local
      | \.envrc(?![\w-])
      | \.netrc(?![\w-])
      | \.git-credentials(?![\w-])
      | [\w.-]+\.(?:pem|p12|pfx)(?![\w-])     # private keys and certificates
      | id_(?:rsa|dsa|ecdsa|ed25519)(?![\w-])
      | (?:secrets|\.ssh|\.aws)(?=[/\\'"]|$)  # folders of secrets
      | \.data(?=[/\\'"]|$)                   # backend/.data: real workers' answers
    )
    """,
    re.VERBOSE | re.IGNORECASE,
)

SHELL_OPERATORS: str = "();<>|&\n"
COMMAND_WRAPPERS: frozenset[str] = frozenset(
    {"env", "command", "time", "sudo", "nohup", "exec"}
)
ENVIRONMENT_ASSIGNMENT_PATTERN: re.Pattern[str] = re.compile(r"[A-Za-z_]\w*=")
GIT_OPTIONS_WITH_A_VALUE: frozenset[str] = frozenset(
    {"-C", "-c", "--git-dir", "--work-tree"}
)
# Commands that only write a message. Their text may mention `.env` freely.
MESSAGE_SUBCOMMANDS: frozenset[tuple[str, ...]] = frozenset(
    {("git", "commit"), ("git", "tag"), ("gh", "pr"), ("gh", "issue")}
)
SUBCOMMANDS_THAT_CHANGE_A_BRANCH: frozenset[str] = frozenset(
    {"commit", "merge", "cherry-pick", "revert", "am", "rebase", "push"}
)

type Words = list[str]
"""One simple command, split into words, such as `["git", "push", "origin"]`."""

type GitRule = Callable[[Words, str], str | None]
"""A check on a git subcommand's words and the branch it runs on: why it is blocked."""


def split_into_simple_commands(command: str) -> list[Words]:
    """Split a command line into simple commands, keeping quoted text in one word.

    Quotes and backslashes are kept as written, because PowerShell and Windows paths
    use backslashes as folder separators.

    Args:
        command: The full command line. It may chain commands with `&&`, `||`, `;`,
            `|`, `&` or new lines, and group them with brackets.

    Returns:
        The words of each simple command, without the operators between them.
    """
    lexer = shlex.shlex(command, posix=False, punctuation_chars=SHELL_OPERATORS)
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    try:
        all_words: Words = list(lexer)
    except ValueError:  # an unclosed quote: fall back to plain spaces
        all_words = command.split()
    simple_commands: list[Words] = [[]]
    for word in all_words:
        if set(word) <= set(SHELL_OPERATORS):
            simple_commands.append([])
        else:
            simple_commands[-1].append(word)
    return [words for words in simple_commands if words]


def unquoted(word: str) -> str:
    """Remove the quotes around a word, as a shell would."""
    return word.strip("'\"")


def program_and_arguments(words: Words) -> Words:
    """Drop `NAME=value` settings and wrappers such as `env` or `sudo` before a program.

    Args:
        words: One simple command's words, such as `["HUSKY=0", "git", "commit"]`.

    Returns:
        The program's name, without folder or `.exe`, then its unquoted arguments.
    """
    position: int = 0
    while position < len(words) and (
        ENVIRONMENT_ASSIGNMENT_PATTERN.match(words[position])
        or words[position] in COMMAND_WRAPPERS
    ):
        position += 1
    if position == len(words):
        return []
    program: str = Path(unquoted(words[position]).replace("\\", "/")).stem.lower()
    return [program, *(unquoted(word) for word in words[position + 1 :])]


def git_subcommand(arguments: Words) -> Words:
    """Skip git's own options, such as `-C folder`, to reach the subcommand.

    Args:
        arguments: Everything after `git`, such as `["-C", "repo", "push"]`.

    Returns:
        The subcommand and its arguments (`["push"]`), or [] when there is none.
    """
    position: int = 0
    while position < len(arguments) and arguments[position].startswith("-"):
        position += 2 if arguments[position] in GIT_OPTIONS_WITH_A_VALUE else 1
    return arguments[position:]


def secret_named_in(text: str) -> str | None:
    """Find the first secret or worker-data name in some text.

    Args:
        text: A file path or one word of a shell command.

    Returns:
        The name that matched, or None when the text names no secret.
    """
    match: re.Match[str] | None = SECRET_PATH_PATTERN.search(text)
    return match.group(0) if match else None


def secret_reason(secret: str) -> str:
    """Say why a call that names a secret is blocked."""
    return f"{secret} may hold secrets or worker data. Agents never read or change it."


def is_short_option_with(letter: str, word: str) -> bool:
    """Tell whether a word is a group of short options that includes a letter.

    Args:
        letter: The option's letter, such as `f` for `-f`.
        word: One argument, such as `-fu`.

    Returns:
        True for `-f`, `-fu` or `-uf` when the letter is `f`.
    """
    return re.fullmatch(rf"-[a-zA-Z]*{letter}[a-zA-Z]*", word) is not None


def block_no_verify(git_words: Words, branch: str) -> str | None:
    """Block skipping git's own checks: `--no-verify`, or `-n` on a commit."""
    names_no_verify: bool = any(
        word.startswith("--no-v") and "--no-verify".startswith(word)
        for word in git_words
    )
    commits_with_n: bool = git_words[0] == "commit" and any(
        is_short_option_with("n", word) for word in git_words
    )
    if names_no_verify or commits_with_n:
        return "--no-verify skips the repo's checks. Fix what the check reports."
    return None


def block_force_push(git_words: Words, branch: str) -> str | None:
    """Block a push that could overwrite or delete commits already on GitHub."""
    forces: bool = any(
        word.startswith(("--forc", "--mirror", "+")) or is_short_option_with("f", word)
        for word in git_words[1:]
    )
    if git_words[0] == "push" and forces:
        return "A force push can throw away commits. Ask the human to do it."
    return None


def block_push_to_main(git_words: Words, branch: str) -> str | None:
    """Block a push to `main`: `git push origin main`, `HEAD:main` or `--all`."""
    main_names: tuple[str, ...] = (PROTECTED_BRANCH, f"refs/heads/{PROTECTED_BRANCH}")
    targets_main: bool = any(
        word == "--all" or word.split(":")[-1] in main_names for word in git_words[1:]
    )
    if git_words[0] == "push" and targets_main:
        return f"Never push to {PROTECTED_BRANCH}. Push the task branch (AGENTS.md)."
    return None


def block_work_on_main(git_words: Words, branch: str) -> str | None:
    """Block a commit, merge or push made while `main` is checked out."""
    if git_words[0] in SUBCOMMANDS_THAT_CHANGE_A_BRANCH and branch == PROTECTED_BRANCH:
        return f"You are on {PROTECTED_BRANCH}. Create the task branch (AGENTS.md)."
    return None


GIT_RULES: tuple[GitRule, ...] = (
    block_no_verify,
    block_force_push,
    block_push_to_main,
    block_work_on_main,
)


def branch_after(git_words: Words, branch: str) -> str:
    """Work out which branch is checked out after a `git checkout` or `git switch`.

    Args:
        git_words: A git subcommand and its arguments, such as `["switch", "main"]`.
        branch: The branch checked out before it.

    Returns:
        The branch it switches to, or the same branch for any other command.
    """
    if git_words[0] not in ("checkout", "switch") or "--" in git_words:
        return branch
    names: Words = [word for word in git_words[1:] if not word.startswith("-")]
    return names[0] if names else branch


def reason_to_block_command(command: str, current_branch: str) -> str | None:
    """Decide whether a shell command must be blocked.

    Args:
        command: The full command line Claude wants to run, in Bash or PowerShell.
        current_branch: The branch checked out where the command starts, or "".

    Returns:
        Why the command is blocked, or None when it may run.
    """
    branch: str = current_branch
    for words in split_into_simple_commands(command):
        program_words: Words = program_and_arguments(words)
        if tuple(program_words[:2]) not in MESSAGE_SUBCOMMANDS:
            for word in words:
                if secret := secret_named_in(word):
                    return secret_reason(secret)
        if program_words[:3] == ["gh", "pr", "merge"]:
            return "Only the human merges a pull request (AGENTS.md)."
        if program_words[:1] != ["git"]:
            continue
        git_words: Words = git_subcommand(program_words[1:])
        if not git_words:
            continue
        for rule in GIT_RULES:
            if reason := rule(git_words, branch):
                return reason
        branch = branch_after(git_words, branch)
    return None


def reason_to_block_tool_call(
    tool_name: str, tool_input: Mapping[str, Any], current_branch: str
) -> str | None:
    """Decide whether a tool call must be blocked.

    Args:
        tool_name: The tool Claude wants to use, such as `Bash`, `Read` or `Glob`.
        tool_input: The tool's arguments, as Claude Code sends them.
        current_branch: The branch checked out where Claude is working, or "".

    Returns:
        Why the call is blocked, or None when it may go ahead.
    """
    path_fields: tuple[str, ...] = (
        (*PATH_FIELDS, "pattern") if tool_name == "Glob" else PATH_FIELDS
    )
    for field in path_fields:
        path: object = tool_input.get(field)
        if isinstance(path, str) and (secret := secret_named_in(path)):
            return secret_reason(secret)
    command: object = tool_input.get("command")
    if tool_name in SHELL_TOOLS and isinstance(command, str):
        return reason_to_block_command(command, current_branch)
    return None


def current_branch_in(folder: str) -> str:
    """Ask git which branch is checked out.

    Args:
        folder: The folder Claude is working in, or "" for the current folder.

    Returns:
        The branch name, or "" when git can't tell (no repository, no git, no folder).
    """
    try:
        result: subprocess.CompletedProcess[str] = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=folder or None,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError:
        return ""
    return result.stdout.strip()


def main() -> int:
    """Read the tool call from standard input and block it if a rule says so.

    Returns:
        2 to block the call, otherwise 0.
    """
    hook_input: dict[str, Any] = json.load(sys.stdin.buffer)  # Claude sends UTF-8
    tool_name: str = hook_input.get("tool_name", "")
    tool_input: dict[str, Any] = hook_input.get("tool_input") or {}
    command_text: str = str(tool_input.get("command", ""))
    needs_branch: bool = tool_name in SHELL_TOOLS and "git" in command_text
    current_branch: str = (
        current_branch_in(hook_input.get("cwd", "")) if needs_branch else ""
    )
    reason: str | None = reason_to_block_tool_call(
        tool_name, tool_input, current_branch
    )
    if reason is None:
        return 0
    print(
        f"Blocked by scripts/claude_hooks/guard_tool_use.py: {reason}", file=sys.stderr
    )
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:  # a broken guard must not wave calls through
        print(
            f"guard_tool_use.py failed, so the call is blocked: {error!r}",
            file=sys.stderr,
        )
        sys.exit(2)
