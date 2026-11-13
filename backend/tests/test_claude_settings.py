"""Tests that `.claude/settings.json` is valid and runs the hooks that exist."""

import json
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT: Path = Path(__file__).resolve().parents[2]
SETTINGS: dict[str, Any] = json.loads(
    (REPO_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8")
)
HOOK_GROUPS: list[dict[str, Any]] = [
    group for groups in SETTINGS["hooks"].values() for group in groups
]


@pytest.mark.parametrize("group", HOOK_GROUPS)
def test_every_hook_runs_a_script_that_exists(group: dict[str, Any]) -> None:
    """A moved or renamed hook script would make uv fail on every tool call."""
    for hook in group["hooks"]:
        script: str = hook["args"][-1].replace("${CLAUDE_PROJECT_DIR}", str(REPO_ROOT))

        assert hook["command"] == "uv"
        assert Path(script).is_file()


def test_the_guard_sees_both_shells() -> None:
    """On Windows, Claude Code runs commands with PowerShell rather than Bash."""
    guard_matcher: str = SETTINGS["hooks"]["PreToolUse"][0]["matcher"]

    assert {"Bash", "PowerShell"} <= set(guard_matcher.split("|"))
