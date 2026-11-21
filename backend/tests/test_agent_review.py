"""Exercise the CI review gate without credentials or GitHub writes."""

import json
import subprocess
from pathlib import Path

import pytest

ROOT: Path = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    ("author", "action", "sender", "draft", "fork", "branch", "expected"),
    [
        ("Jake", "opened", "claude[bot]", False, False, "claude/task", True),
        ("Jake", "synchronize", "claude[bot]", False, False, "claude/task", False),
        ("Jake", "synchronize", "Jake", False, False, "chatgpt/task", True),
        ("Jake", "ready_for_review", "Jake", False, False, "task", True),
        ("Jake", "reopened", "Jake", False, False, "task", True),
        ("Jake", "opened", "Jake", True, False, "task", False),
        ("Jake", "opened", "Jake", False, True, "task", False),
        ("Jake", "opened", "Jake", False, False, "main", False),
        ("Jake", "closed", "Jake", False, False, "task", False),
        (
            "dependabot[bot]",
            "opened",
            "dependabot[bot]",
            False,
            False,
            "dependabot/npm/vite",
            False,
        ),
        (
            "dependabot[bot]",
            "synchronize",
            "Jake",
            False,
            False,
            "dependabot/npm/vite",
            False,
        ),
    ],
)
def test_review_gate_skips_drafts_forks_main_dependabot_and_its_own_pushes(
    author: str,
    action: str,
    sender: str,
    draft: bool,
    fork: bool,
    branch: str,
    expected: bool,
) -> None:
    """Allow ordinary PR changes; reject drafts, forks, Dependabot and reviewer loops.

    Args:
        author: Account that opened the PR.
        action: GitHub PR event action.
        sender: Account responsible for the event, not the original PR author.
        draft: Whether the PR is unfinished.
        fork: Whether its source belongs to another repository.
        branch: Source branch.
        expected: Whether a reviewer may start.
    """
    payload: dict[str, object] = {
        "action": action,
        "sender": {"login": sender},
        "repository": {"full_name": "example/repo", "default_branch": "main"},
        "pull_request": {
            "user": {"login": author},
            "draft": draft,
            "head": {
                "ref": branch,
                "repo": {"full_name": "example/fork" if fork else "example/repo"},
            },
        },
    }
    result: subprocess.CompletedProcess[str] = subprocess.run(
        [
            "node",
            "-e",
            "const gate=require('./scripts/agent_review.cjs');"
            "console.log(gate(JSON.parse(process.argv[1])));",
            json.dumps({"eventName": "pull_request", "payload": payload}),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == str(expected).lower()
