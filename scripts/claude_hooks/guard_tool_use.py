# /// script
# requires-python = ">=3.13"
# ///
"""Stop a Claude Code tool call that would touch a secret or break the repo's git rules.

Claude Code runs this before each file tool and shell command (a `PreToolUse` hook,
set in `.claude/settings.json`) and passes the call as JSON on standard input. Exit
code 2 blocks the call, and what is printed to standard error is the reason Claude
sees. Exit code 0 leaves the decision to the normal permission rules.

The deny rules in `.claude/settings.json` only cover Claude's file tools and simple
commands such as `cat .env`. This hook reads the whole text of every shell command,
so `python -c "print(open('.env').read())"` is caught too. A commit message or pull
request body that names a secret is blocked as well: write the text to a file with
the Write tool and pass the file (`git commit -F`, `gh pr create --body-file`).

It is a soft guard. It matches words, so a command that reads a file without naming
it, or a script that opens one, gets past it. `docs/decisions.md` lists the limits.
"""

import json
import re
import subprocess
import sys
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

PROTECTED_BRANCH: str = "main"
SHELL_TOOLS: frozenset[str] = frozenset({"Bash", "PowerShell"})
PATH_FIELDS: tuple[str, ...] = ("file_path", "path", "notebook_path", "glob")
MERGE_TOOLS: frozenset[str] = frozenset({"mcp__github__merge_pull_request"})
MERGE_REASON: str = "Only the human merges a pull request (AGENTS.md)."

# A name that holds secrets or worker data. The look-behind and look-aheads only match
# whole names, so `.venv`, `os.environ`, `process.env.PORT` and `jq .data` don't
# match. Folders only match beside a `/` or `\`. Key files ending in `.key` are left
# to the deny rules, because `event.key` is ordinary code.
SECRET_PATH_PATTERN: re.Pattern[str] = re.compile(
    r"""
    (?<![\w.-])
    (
        \.env(?:\.[\w.-]+)?(?![\w-])             # .env, .env.local
      | \.envrc(?![\w-])
      | \.netrc(?![\w-])
      | \.git-credentials(?![\w-])
      | [\w.-]+\.(?:pem|p12|pfx)(?![\w-])       # private keys and certificates
      | id_(?:rsa|dsa|ecdsa|ed25519)(?![\w-])
      | secrets[/\\]
      | (?<=/)\.(?:ssh|aws|data)(?![\w.-])      # ~/.ssh, backend/.data
      | \.(?:ssh|aws|data)[/\\]                 # .data/take5.sqlite3
    )
    """,
    re.VERBOSE | re.IGNORECASE,
)

# A quoted string on one line. Quotes that span lines are left alone, because an
# apostrophe in a comment or a heredoc would otherwise pair with a later quote and
# hide the commands between them.
QUOTED_TEXT_PATTERN: re.Pattern[str] = re.compile(r"'[^'\n]*'|\"[^\"\n]*\"")
SHELL_SEPARATOR_PATTERN: re.Pattern[str] = re.compile(r"&&|\|\||[;|&(){}`<>!\n]")
GIT_PROGRAMS: frozenset[str] = frozenset({"git", "gh"})
GIT_OPTIONS_WITH_A_VALUE: frozenset[str] = frozenset(
    {"-C", "-c", "--git-dir", "--work-tree"}
)
MAIN_NAMES: frozenset[str] = frozenset(
    {PROTECTED_BRANCH, f"heads/{PROTECTED_BRANCH}", f"refs/heads/{PROTECTED_BRANCH}"}
)
SUBCOMMANDS_THAT_CHANGE_A_BRANCH: frozenset[str] = frozenset(
    {"commit", "merge", "cherry-pick", "revert", "am", "rebase", "push"}
)
# `-n` is `--no-verify` on a commit. These are the commit options that take no value
# and may share its dash, as in `-anm`.
COMMIT_NO_VERIFY_PATTERN: re.Pattern[str] = re.compile(r"-[aqsv]*n[aqsvm]*")

type Words = list[str]
"""One simple command, split into words, such as `["git", "push", "origin"]`."""

type GitRule = Callable[[Words, str], str | None]
"""A check on a git subcommand's words and the branch it runs on: why it is blocked."""


def flatten_quoted_text(command: str) -> str:
    """Turn each quoted string into one word, so its contents can't look like commands.

    `git commit -m "fix; git push origin main"` becomes
    `git commit -m fix__git_push_origin_main`. A string that holds `$(...)` or a
    backtick is left as it is, because the shell runs what is inside it.

    Args:
        command: The full command line.

    Returns:
        The command line with spaces and operators inside quotes replaced by `_`.
    """

    def flattened(quoted: re.Match[str]) -> str:
        text: str = quoted.group(0)
        if "$(" in text or "`" in text:
            return text
        return re.sub(r"[\s;|&(){}`<>!]", "_", text[1:-1]) or "_"

    return QUOTED_TEXT_PATTERN.sub(flattened, command)


def split_into_simple_commands(command: str) -> list[Words]:
    """Split a command line into simple commands, each as a list of words.

    Args:
        command: The full command line. It may chain commands with `&&`, `||`, `;`,
            `|`, `&` or new lines, continue lines with a backslash, and group
            commands with brackets or braces.

    Returns:
        The words of each simple command, without the operators between them.
    """
    joined_lines: str = command.replace("\\\n", " ")
    parts: list[str] = SHELL_SEPARATOR_PATTERN.split(flatten_quoted_text(joined_lines))
    return [words for part in parts if (words := part.split())]


def program_name(word: str) -> str:
    """Give a program's name without folder, quotes or `.exe`, such as `git`."""
    return Path(word.strip("'\"").replace("\\", "/")).stem.lower()


def program_and_arguments(words: Words) -> Words:
    """Find git or gh in a simple command, past wrappers such as `sudo -u x` or `if`.

    Args:
        words: One simple command's words, such as `["HUSKY=0", "git", "commit"]`.

    Returns:
        `git` or `gh`, then its arguments, or [] when the command runs neither.
    """
    for position, word in enumerate(words):
        if program_name(word) in GIT_PROGRAMS:
            return [program_name(word), *words[position + 1 :]]
    return []


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
        text: A file path, or the whole text of a shell command.

    Returns:
        The name that matched, or None when the text names no secret.
    """
    match: re.Match[str] | None = SECRET_PATH_PATTERN.search(text)
    return match.group(0) if match else None


def secret_reason(secret: str) -> str:
    """Say why a call that names a secret is blocked."""
    return (
        f"{secret} may hold secrets or worker data. Agents never read or change it. "
        "If this is only a commit message or PR text, write it to a file and pass that."
    )


def block_no_verify(git_words: Words, branch: str) -> str | None:
    """Block skipping git's own checks: `--no-verify`, or `-n` on a commit."""
    names_no_verify: bool = any(
        word.startswith("--no-v") and "--no-verify".startswith(word)
        for word in git_words
    )
    commits_with_n: bool = git_words[0] == "commit" and any(
        COMMIT_NO_VERIFY_PATTERN.fullmatch(word) for word in git_words
    )
    if names_no_verify or commits_with_n:
        return "--no-verify skips the repo's checks. Fix what the check reports."
    return None


def block_force_push(git_words: Words, branch: str) -> str | None:
    """Block a push that could overwrite or delete commits already on GitHub."""
    forces: bool = any(
        word.startswith(("--forc", "--mirror", "+"))
        or re.fullmatch(r"-[a-zA-Z]*f[a-zA-Z]*", word) is not None
        for word in git_words[1:]
    )
    if git_words[0] == "push" and forces:
        return "A force push can throw away commits. Ask the human to do it."
    return None


def block_push_to_main(git_words: Words, branch: str) -> str | None:
    """Block a push to `main`: `git push origin main`, `HEAD:main` or `--all`."""
    targets_main: bool = any(
        word in ("--all", "--branches") or word.split(":")[-1] in MAIN_NAMES
        for word in git_words[1:]
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


def looks_like_a_file(name: str) -> bool:
    """Tell a file argument (`.`, `docs/spec.md`) from a branch name (`claude/0011`)."""
    return name == "." or "." in Path(name).name


def branch_after(git_words: Words, branch: str) -> str:
    """Work out which branch is checked out after a `git checkout` or `git switch`.

    Args:
        git_words: A git subcommand and its arguments, such as `["switch", "main"]`.
        branch: The branch checked out before it.

    Returns:
        The branch it switches to, or the same branch when it only restores files.
    """
    if git_words[0] not in ("checkout", "switch") or "--" in git_words:
        return branch
    for new_branch_option in ("-b", "-B", "-c", "-C"):
        if new_branch_option in git_words[:-1]:
            return git_words[git_words.index(new_branch_option) + 1]
    names: Words = [word for word in git_words[1:] if not word.startswith("-")]
    if not names or (git_words[0] == "checkout" and looks_like_a_file(names[-1])):
        return branch
    return names[0]


def merges_a_pull_request(gh_words: Words) -> bool:
    """Tell whether a `gh` command merges: `gh pr merge 13` or `gh api .../merge`."""
    after_pr: Words = gh_words[gh_words.index("pr") + 1 :] if "pr" in gh_words else []
    return after_pr[:1] == ["merge"] or any(
        word.endswith("/merge") for word in gh_words
    )


def reason_to_block_command(command: str, current_branch: str) -> str | None:
    """Decide whether a shell command must be blocked.

    Args:
        command: The full command line Claude wants to run, in Bash or PowerShell.
        current_branch: The branch checked out where the command starts, or "".

    Returns:
        Why the command is blocked, or None when it may run.
    """
    if secret := secret_named_in(command):
        return secret_reason(secret)
    branch: str = current_branch
    for words in split_into_simple_commands(command):
        program_words: Words = program_and_arguments(words)
        if program_words[:1] == ["gh"] and merges_a_pull_request(program_words):
            return MERGE_REASON
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
    if tool_name in MERGE_TOOLS:
        return MERGE_REASON
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
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
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
    print(f"Blocked by {Path(__file__).name}: {reason}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:  # a broken guard must not wave calls through
        print(
            f"The guard failed, so the call is blocked: {error!r}",
            file=sys.stderr,
        )
        sys.exit(2)
