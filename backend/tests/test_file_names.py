"""Tests that every file name in the repo works the same on Windows as on Linux."""

import subprocess
from collections import defaultdict
from pathlib import Path, PurePosixPath

REPO_ROOT: Path = Path(__file__).resolve().parents[2]


def names_differing_only_by_case(paths: list[str]) -> list[list[str]]:
    """Find files in one folder whose names differ only by case.

    The last extension is ignored. Windows ignores case, and an import such as
    `./TimeLeft` tries each extension, so `timeLeft.ts` beside `TimeLeft.tsx` loads the
    wrong file there and never on Linux.

    Args:
        paths: File paths relative to the repo root, with forward slashes.

    Returns:
        Each group of clashing paths, sorted. Empty when nothing clashes.
    """
    by_folder_and_stem: defaultdict[str, list[str]] = defaultdict(list)
    for path in paths:
        file: PurePosixPath = PurePosixPath(path)
        by_folder_and_stem[str(file.with_suffix("")).casefold()].append(path)
    return [
        sorted(group)
        for group in by_folder_and_stem.values()
        if len({str(PurePosixPath(path).with_suffix("")) for path in group}) > 1
    ]


def test_a_name_differing_only_by_case_is_found() -> None:
    """The clash that opened the app blank on Windows is caught."""
    clashes: list[list[str]] = names_differing_only_by_case(
        [
            "frontend/src/TimeLeft.tsx",
            "frontend/src/timeLeft.ts",
            "frontend/src/TimeLeft.test.tsx",
        ],
    )

    assert clashes == [["frontend/src/TimeLeft.tsx", "frontend/src/timeLeft.ts"]]


def test_the_same_name_with_other_extensions_is_fine() -> None:
    """`index.ts` beside `index.css`, or the same name in two folders, is no clash."""
    assert not names_differing_only_by_case(
        ["src/index.ts", "src/index.css", "src/a/Card.tsx", "src/b/card.tsx"],
    )


def test_no_two_files_in_the_repo_differ_only_by_case() -> None:
    """No file git tracks has a name that another in its folder matches on Windows."""
    tracked: list[str] = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()

    assert names_differing_only_by_case(tracked) == []
