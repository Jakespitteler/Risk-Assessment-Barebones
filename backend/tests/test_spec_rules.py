"""Tests that every rule in the spec is named by a test, and no test names an old one.

Task 0013.

A rule is a numbered definition in `docs/spec.md`, such as **R1 Rating.** or **V2**.
A test names it by putting the number in a back-end test function's docstring (Ruff
keeps function names lowercase, so a name can't hold it), or in the name of a
front-end `it(...)` or `test(...)`. `it.each` names, comments and module docstrings
don't count, so each rule points to a real test. A rule number a test names that the
spec no longer defines, such as a removed R7, fails too.
"""

import ast
import re
from collections.abc import Iterable
from pathlib import Path

REPO_ROOT: Path = Path(__file__).resolve().parents[2]
SPEC_PATH: Path = REPO_ROOT / "docs" / "spec.md"
BACKEND_TESTS: Path = REPO_ROOT / "backend" / "tests"
FRONTEND: Path = REPO_ROOT / "frontend"

RULE_DEFINITION: re.Pattern[str] = re.compile(r"^\s*- \*\*([A-Z]\d+)\b", re.MULTILINE)
FRONTEND_TEST_NAME: re.Pattern[str] = re.compile(
    r"(?<![\w.])(?:it|test)\(\s*(?P<quote>[\"'`])(?P<name>.*?)(?P=quote)",
    re.DOTALL,
)


def spec_rule_numbers(spec: str) -> list[str]:
    """Find the rule numbers the spec defines, in the order it defines them.

    Args:
        spec: The text of `docs/spec.md`.

    Returns:
        Each rule number, such as "R1", once.
    """
    return list(dict.fromkeys(RULE_DEFINITION.findall(spec)))


def python_test_texts(source: str) -> list[str]:
    """Find each test function's name and docstring in a Python test file.

    Args:
        source: The text of a pytest file.

    Returns:
        For each function whose name starts with `test`, its name and docstring
        together.
    """
    texts: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(
            node,
            ast.FunctionDef | ast.AsyncFunctionDef,
        ) and node.name.startswith("test"):
            texts.append(f"{node.name}\n{ast.get_docstring(node) or ''}")
    return texts


def frontend_test_names(source: str) -> list[str]:
    """Find the name of each Vitest or Playwright test in a front-end test file.

    Args:
        source: The text of a `.test.tsx` or `.spec.ts` file.

    Returns:
        The first string given to each `it(...)` or `test(...)`.
    """
    return [match.group("name") for match in FRONTEND_TEST_NAME.finditer(source)]


def rules_not_named(
    rule_numbers: Iterable[str],
    test_texts: Iterable[str],
) -> list[str]:
    """Find the rule numbers that no test's name or docstring contains as a whole word.

    Args:
        rule_numbers: The spec's rule numbers.
        test_texts: Every test's name and docstring.

    Returns:
        The rule numbers no test names, in the order given.
    """
    all_text: str = "\n".join(test_texts)
    return [rule for rule in rule_numbers if not re.search(rf"\b{rule}\b", all_text)]


def rules_named_but_not_defined(
    rule_numbers: Iterable[str],
    test_texts: Iterable[str],
) -> list[str]:
    """Find rule numbers that tests name but the spec doesn't define.

    A rule number is one of the spec's rule letters (R, V, T, C and K today) and a
    number, so a decision such as D6 or a feature such as F3 is never one.

    Args:
        rule_numbers: The spec's rule numbers.
        test_texts: Every test's name and docstring.

    Returns:
        Each unknown rule number once, sorted.
    """
    defined: set[str] = set(rule_numbers)
    if not defined:
        return []
    rule_letters: str = "".join(sorted({number[0] for number in defined}))
    rule_number: re.Pattern[str] = re.compile(rf"\b[{rule_letters}]\d+\b")
    named: set[str] = {
        number for text in test_texts for number in rule_number.findall(text)
    }
    return sorted(named - defined)


def all_test_texts() -> list[str]:
    """Read every test's name, and each back-end test's docstring.

    This file is left out, since its own tests name rules only as examples.

    Returns:
        One text for each test in the repo.
    """
    texts: list[str] = []
    for path in sorted(BACKEND_TESTS.rglob("test_*.py")):
        if path == Path(__file__).resolve():
            continue
        texts.extend(python_test_texts(path.read_text(encoding="utf-8")))
    frontend_files: list[Path] = [
        *(FRONTEND / "src").rglob("*.test.ts"),
        *(FRONTEND / "src").rglob("*.test.tsx"),
        *(FRONTEND / "e2e").glob("*.spec.ts"),
    ]
    for path in sorted(frontend_files):
        texts.extend(frontend_test_names(path.read_text(encoding="utf-8")))
    return texts


def test_the_spec_rules_are_found() -> None:
    """All 24 rules are read, so a change to the spec's layout can't empty the check."""
    rules: list[str] = spec_rule_numbers(SPEC_PATH.read_text(encoding="utf-8"))

    assert rules == [
        *(f"R{number}" for number in range(1, 7)),
        *(f"V{number}" for number in range(1, 4)),
        *(f"T{number}" for number in range(1, 7)),
        *(f"C{number}" for number in range(1, 7)),
        *(f"K{number}" for number in range(1, 4)),
    ]


def test_every_spec_rule_is_named_by_a_test() -> None:
    """Each rule number in the spec is in at least one test's name or docstring."""
    rules: list[str] = spec_rule_numbers(SPEC_PATH.read_text(encoding="utf-8"))

    missing: list[str] = rules_not_named(rules, all_test_texts())

    assert not missing, (
        f"Spec rules no test names: {', '.join(missing)}. "
        "Put the rule number in a test's name or docstring."
    )


def test_no_test_names_a_rule_the_spec_no_longer_has() -> None:
    """A renumbered or removed rule can't leave tests pointing at nothing."""
    rules: list[str] = spec_rule_numbers(SPEC_PATH.read_text(encoding="utf-8"))

    unknown: list[str] = rules_named_but_not_defined(rules, all_test_texts())

    assert not unknown, (
        f"Tests name rules the spec doesn't define: {', '.join(unknown)}. "
        "Use the spec's current rule numbers."
    )


def test_an_old_rule_number_is_found_but_decisions_and_features_are_not() -> None:
    """R7 is not a rule; D6, F3 and LV12 aren't rule numbers at all."""
    texts: list[str] = ["Controls can't raise it (R6, R7)", "D6 and F3 on LV12 (C4)"]

    assert rules_named_but_not_defined(["R6", "C4"], texts) == ["R7"]


def test_only_rule_definitions_count_as_rules() -> None:
    """A rule mentioned in passing, or a decision such as D6, is not a new rule."""
    spec: str = (
        "- **R1 Rating.** A lookup.\n"
        "- **V2** A hazard has no controls.\n"
        "The after rating counts for R3 (decision D6).\n"
        "| 13 | Rare / Major (10) | R4 |\n"
    )

    assert spec_rule_numbers(spec) == ["R1", "V2"]


def test_a_test_docstring_names_a_rule_but_a_module_docstring_does_not() -> None:
    """Only a test function's own name and docstring tie a rule to that test."""
    source: str = (
        '"""All the challenge rules (C1 to C6)."""\n'
        "\n"
        "def test_a_short_answer_is_refused() -> None:\n"
        '    """One word is not enough (C4)."""\n'
        "\n"
        "def helper_for_c5() -> None:\n"
        '    """Builds a Take 5 (C5)."""\n'
    )

    missing: list[str] = rules_not_named(["C1", "C4", "C5"], python_test_texts(source))

    assert missing == ["C1", "C5"]


def test_vitest_and_playwright_names_are_read() -> None:
    """`it(...)` and `test(...)` names count; a `describe` and a comment don't."""
    source: str = (
        "// Covers T2.\n"
        'test.describe("T3 group", () => {});\n'
        'it("keeps the draft on the phone (K1)", () => {});\n'
        "test('T1: questions stay hidden', async ({ page }) => {});\n"
    )

    names: list[str] = frontend_test_names(source)

    assert names == ["keeps the draft on the phone (K1)", "T1: questions stay hidden"]


def test_a_rule_number_must_be_a_whole_word() -> None:
    """R1 inside R12 or LV12 is not R1."""
    assert rules_not_named(["R1", "V1"], ["Change tyre on LV12 (R12)"]) == ["R1", "V1"]
