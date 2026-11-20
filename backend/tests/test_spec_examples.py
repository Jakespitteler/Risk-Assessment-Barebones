"""Tests that every worked example in the spec has a test named by its number.

Task 0013. The spec's worked examples are the numbered rows under "Worked examples".
A back-end test names one as `test_example_<number>_...`, as AGENTS.md asks. A test that
covers a run of them, named as the tests already do (`test_example_2_to_10_...`,
`test_examples_50_and_51_...`), must also list each example among its cases, as a
`pytest.param` id or an `ids=` entry such as "test_example_3" or "example_50_one_word"
(Jake, 2026-11-19), so a name alone can't claim examples it doesn't check.
"""

import ast
import re
from collections.abc import Iterable
from pathlib import Path
from typing import NamedTuple

REPO_ROOT: Path = Path(__file__).resolve().parents[2]
SPEC_PATH: Path = REPO_ROOT / "docs" / "spec.md"
BACKEND_TESTS: Path = REPO_ROOT / "backend" / "tests"

EXAMPLE_ROW: re.Pattern[str] = re.compile(r"^\| (\d+) \|", re.MULTILINE)
EXAMPLE_TEST_NAME: re.Pattern[str] = re.compile(
    r"^test_examples?_(\d+)(?:_(to|and)_(\d+))?(?:_|$)",
)
EXAMPLE_CASE_ID: re.Pattern[str] = re.compile(r"^(?:test_)?example_(\d+)(?:_|$)")


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


class ExampleTest(NamedTuple):
    """A back-end test: its name and the examples its cases list."""

    name: str
    listed_examples: frozenset[int]


def case_ids(test: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    """Read the ids a test gives its cases, and nothing else from its decorators.

    Args:
        test: The test function, with its decorators.

    Returns:
        Each `id=` given to a `pytest.param(...)`, and each string in a
        `parametrize(..., ids=...)` list or tuple. An `id=` anywhere else, such as
        inside a case's value, is not a case id.
    """
    ids: list[str] = []
    for decorator in test.decorator_list:
        for node in ast.walk(decorator):
            if not isinstance(node, ast.Call):
                continue
            called: str = node.func.attr if isinstance(node.func, ast.Attribute) else ""
            for keyword in node.keywords:
                if (
                    called == "param"
                    and keyword.arg == "id"
                    and isinstance(keyword.value, ast.Constant)
                ):
                    ids.append(str(keyword.value.value))
                if (
                    called == "parametrize"
                    and keyword.arg == "ids"
                    and isinstance(keyword.value, ast.List | ast.Tuple)
                ):
                    ids.extend(
                        str(item.value)
                        for item in keyword.value.elts
                        if isinstance(item, ast.Constant)
                    )
    return ids


def listed_examples(test: ast.FunctionDef | ast.AsyncFunctionDef) -> frozenset[int]:
    """Read the example numbers a test's cases list in their ids.

    Args:
        test: The test function, with its decorators.

    Returns:
        Each number from an id such as "test_example_3" or "example_50_one_word".
    """
    return frozenset(
        int(match.group(1))
        for case_id in case_ids(test)
        if (match := EXAMPLE_CASE_ID.match(case_id)) is not None
    )


def python_tests(source: str) -> list[ExampleTest]:
    """Find each test function in a Python test file, with the examples it lists.

    Args:
        source: The text of a pytest file.

    Returns:
        One entry for each function whose name starts with `test`.
    """
    return [
        ExampleTest(node.name, listed_examples(node))
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        and node.name.startswith("test")
    ]


def examples_covered(test: ExampleTest) -> set[int]:
    """Say which worked examples a test covers.

    A test named for one example covers it. A test named for a run covers only the
    examples in the run that its cases list.

    Args:
        test: The test.

    Returns:
        The example numbers it covers.
    """
    named: set[int] = examples_in_test_name(test.name)
    if len(named) <= 1:
        return named
    return named & test.listed_examples


def unlisted_examples_in_runs(tests: Iterable[ExampleTest]) -> dict[str, list[int]]:
    """Find run tests whose names claim examples their cases don't list.

    Args:
        tests: Every back-end test.

    Returns:
        Each such test's name, with the claimed numbers it doesn't list.
    """
    unlisted: dict[str, list[int]] = {}
    for test in tests:
        named: set[int] = examples_in_test_name(test.name)
        missing: list[int] = sorted(named - test.listed_examples)
        if len(named) > 1 and missing:
            unlisted[test.name] = missing
    return unlisted


def examples_without_a_test(
    example_numbers: Iterable[int],
    tests: Iterable[ExampleTest],
) -> list[int]:
    """Find the worked examples no test covers.

    Args:
        example_numbers: The spec's worked example numbers.
        tests: Every back-end test.

    Returns:
        The uncovered example numbers, in the order given.
    """
    covered: set[int] = {number for test in tests for number in examples_covered(test)}
    return [number for number in example_numbers if number not in covered]


def all_backend_tests() -> list[ExampleTest]:
    """Read every back-end test function.

    Returns:
        One entry for each test function.
    """
    tests: list[ExampleTest] = []
    for path in sorted(BACKEND_TESTS.rglob("test_*.py")):
        tests.extend(python_tests(path.read_text(encoding="utf-8")))
    return tests


def test_the_worked_examples_are_found() -> None:
    """All 118 are read, so a change to the spec's layout can't empty the check."""
    examples: list[int] = worked_example_numbers(SPEC_PATH.read_text(encoding="utf-8"))

    assert examples == list(range(1, 119))


def test_every_worked_example_has_a_test_named_by_its_number() -> None:
    """Each example in the spec is covered by a `test_example_<number>` test."""
    examples: list[int] = worked_example_numbers(SPEC_PATH.read_text(encoding="utf-8"))

    missing: list[int] = examples_without_a_test(examples, all_backend_tests())

    assert not missing, (
        f"Worked examples with no test named for them: {missing}. "
        "Name a test `test_example_<number>_...`."
    )


def test_every_run_test_lists_each_example_it_names() -> None:
    """`test_example_2_to_10_...` has a case for each of examples 2 to 10."""
    unlisted: dict[str, list[int]] = unlisted_examples_in_runs(all_backend_tests())

    assert not unlisted, (
        f"Tests named for examples their cases don't list: {unlisted}. Give each "
        "example its own case, with an id such as `test_example_3`."
    )


def test_a_run_of_examples_in_a_name_means_each_one() -> None:
    """`2_to_10` is nine examples, `50_and_51` two; `17x` and no number mean none."""
    assert examples_in_test_name("test_example_2_to_10_bands") == set(range(2, 11))
    assert examples_in_test_name("test_examples_50_and_51_refused") == {50, 51}
    assert examples_in_test_name("test_example_7_on_the_threshold") == {7}
    assert examples_in_test_name("test_the_jha_threshold_is_11") == set()
    assert examples_in_test_name("test_example_17x") == set()


def test_a_missing_example_is_named() -> None:
    """The failure says which numbers have no test."""
    tests: list[ExampleTest] = [
        ExampleTest("test_example_1_lowest", frozenset()),
        ExampleTest("test_examples_3_to_4_bands", frozenset({3, 4})),
    ]

    assert examples_without_a_test([1, 2, 3, 4, 5], tests) == [2, 5]


def test_only_case_ids_list_examples() -> None:
    """A case's value, an argument name or an `id=` inside a value is not an id."""
    source: str = (
        "@pytest.mark.parametrize(\n"
        '    "example_2_input",\n'
        '    ["example_3", pytest.param(Hazard(id="example_4"), id="case_b")],\n'
        '    ids=("case_a", "test_example_5"),\n'
        ")\n"
        "def test_example_2_to_5_values(example_2_input: str) -> None:\n"
        "    pass\n"
    )

    (test,) = python_tests(source)

    assert test.listed_examples == {5}


def test_a_run_name_covers_only_the_examples_its_cases_list() -> None:
    """A name like `test_example_1_to_87` can't cover examples it has no case for."""
    source: str = (
        "@pytest.mark.parametrize(\n"
        '    "answer",\n'
        '    [pytest.param("Yes", id="test_example_1_short")],\n'
        '    ids=["ignored"],\n'
        ")\n"
        "def test_example_1_to_3_answers(answer: str) -> None:\n"
        "    pass\n"
    )

    (test,) = python_tests(source)

    assert test.listed_examples == {1}
    assert examples_covered(test) == {1}
    assert unlisted_examples_in_runs([test]) == {"test_example_1_to_3_answers": [2, 3]}
