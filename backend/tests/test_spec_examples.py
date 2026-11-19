"""Tests that every worked example in the spec has a test named by its number.

Task 0013. The spec's worked examples are the numbered rows under "Worked examples".
A back-end test names one as `test_example_<number>_...`, or a run of them as
`test_example_2_to_10_...`, `test_examples_50_to_52_...` or
`test_examples_50_and_51_...`, as AGENTS.md asks.
"""

import ast
import re
from collections.abc import Iterable
from pathlib import Path

REPO_ROOT: Path = Path(__file__).resolve().parents[2]
SPEC_PATH: Path = REPO_ROOT / "docs" / "spec.md"
BACKEND_TESTS: Path = REPO_ROOT / "backend" / "tests"

EXAMPLE_ROW: re.Pattern[str] = re.compile(r"^\| (\d+) \|", re.MULTILINE)
EXAMPLE_TEST_NAME: re.Pattern[str] = re.compile(
    r"^test_examples?_(\d+)(?:_(to|and)_(\d+))?(?:_|$)",
)


def worked_example_numbers(spec: str) -> list[int]:
    """Find the numbers of the spec's worked examples.

    Args:
        spec: The text of `docs/spec.md`.

    Returns:
        Each example's number, sorted.
    """
    start: int = spec.index("### Worked examples")
    end: int = spec.index("\n## ", start)
    return sorted({int(number) for number in EXAMPLE_ROW.findall(spec[start:end])})


def examples_in_test_name(test_name: str) -> set[int]:
    """Read which worked examples a test's name says it covers.

    Args:
        test_name: A test function's name, such as "test_example_2_to_10_bands".

    Returns:
        The example numbers, or none when the name doesn't start with an example.
    """
    match: re.Match[str] | None = EXAMPLE_TEST_NAME.match(test_name)
    if match is None:
        return set()
    first: int = int(match.group(1))
    if match.group(2) is None:
        return {first}
    last: int = int(match.group(3))
    if match.group(2) == "and":
        return {first, last}
    return set(range(first, last + 1))


def python_test_names(source: str) -> list[str]:
    """Find the name of each test function in a Python test file.

    Args:
        source: The text of a pytest file.

    Returns:
        Each name that starts with `test`.
    """
    return [
        node.name
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        and node.name.startswith("test")
    ]


def examples_without_a_test(
    example_numbers: Iterable[int],
    test_names: Iterable[str],
) -> list[int]:
    """Find the worked examples no test's name covers.

    Args:
        example_numbers: The spec's worked example numbers.
        test_names: Every back-end test function's name.

    Returns:
        The uncovered example numbers, in the order given.
    """
    covered: set[int] = {
        number for name in test_names for number in examples_in_test_name(name)
    }
    return [number for number in example_numbers if number not in covered]


def all_backend_test_names() -> list[str]:
    """Read every back-end test function's name.

    Returns:
        One name for each test function.
    """
    names: list[str] = []
    for path in sorted(BACKEND_TESTS.rglob("test_*.py")):
        names.extend(python_test_names(path.read_text(encoding="utf-8")))
    return names


def test_the_worked_examples_are_found() -> None:
    """All 87 are read, so a change to the spec's layout can't empty the check."""
    examples: list[int] = worked_example_numbers(SPEC_PATH.read_text(encoding="utf-8"))

    assert examples == list(range(1, 88))


def test_every_worked_example_has_a_test_named_by_its_number() -> None:
    """Each example in the spec is covered by a `test_example_<number>` test."""
    examples: list[int] = worked_example_numbers(SPEC_PATH.read_text(encoding="utf-8"))

    missing: list[int] = examples_without_a_test(examples, all_backend_test_names())

    assert not missing, (
        f"Worked examples with no test named for them: {missing}. "
        "Name a test `test_example_<number>_...`."
    )


def test_a_run_of_examples_in_a_name_covers_each_one() -> None:
    """`2_to_10` is nine examples; `50_and_51` is two; a later number is not one."""
    assert examples_in_test_name("test_example_2_to_10_bands") == set(range(2, 11))
    assert examples_in_test_name("test_examples_50_and_51_refused") == {50, 51}
    assert examples_in_test_name("test_example_7_on_the_threshold") == {7}
    assert examples_in_test_name("test_the_jha_threshold_is_11") == set()
    assert examples_in_test_name("test_example_17x") == set()


def test_a_missing_example_is_named() -> None:
    """The failure says which numbers have no test."""
    names: list[str] = ["test_example_1_lowest", "test_examples_3_to_4_bands"]

    assert examples_without_a_test([1, 2, 3, 4, 5], names) == [2, 5]
