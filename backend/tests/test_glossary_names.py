"""Tests that every code name in the glossary still exists in the code (task 0013).

`docs/glossary.md` gives each spec term its name in the back end and the front end. A
rename that forgets the glossary makes this fail with the names it can't find.

- A back-end name is looked up in `backend/src/risk_assessment` by reading the code,
  not running it: a class, function or constant (`Take5`, `rate`, `BOOKLET_MATRIX`), a
  class's field or method (`Hazard.covers`), a field or parameter name on its own
  (`location`, `submission_id`), or a file (`fix.py`, `ai/providers/claude.py`).
- A front-end name is a file under `frontend/src` (`Take5Form`), a name it exports
  (`useTake5Draft`, `StoredDraft`), or a field of the generated API types
  (`worker_name`).
"""

import ast
import re
from collections.abc import Iterable
from pathlib import Path

REPO_ROOT: Path = Path(__file__).resolve().parents[2]
GLOSSARY_PATH: Path = REPO_ROOT / "docs" / "glossary.md"
BACKEND_PACKAGE: Path = REPO_ROOT / "backend" / "src" / "risk_assessment"
FRONTEND_SOURCE: Path = REPO_ROOT / "frontend" / "src"
API_TYPES_PATH: Path = FRONTEND_SOURCE / "api" / "schema.d.ts"

CODE_NAME: re.Pattern[str] = re.compile(r"`([^`]+)`")
FRONTEND_EXPORT: re.Pattern[str] = re.compile(
    r"export\s+(?:default\s+)?(?:async\s+)?"
    r"(?:function|const|let|class|type|interface|enum)\s+(\w+)",
)
API_FIELD: re.Pattern[str] = re.compile(r"^\s*(\w+)\??:", re.MULTILINE)
BACKEND_COLUMN: int = 2
FRONTEND_COLUMN: int = 3


def glossary_code_names(glossary: str, column: int) -> set[str]:
    """Read the code names in one column of the glossary's tables.

    Args:
        glossary: The text of `docs/glossary.md`.
        column: The column to read, counting from 0: 2 is the back end, 3 the front end.

    Returns:
        Each name written as code in that column.
    """
    names: set[str] = set()
    for line in glossary.splitlines():
        cells: list[str] = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if not line.startswith("| ") or len(cells) <= column or cells[0] == "Term":
            continue
        names.update(CODE_NAME.findall(cells[column]))
    return names


def python_names(source: str) -> set[str]:
    """Find every name a Python module defines.

    Args:
        source: The text of a module.

    Returns:
        Its top-level classes, functions and constants; each class member as both
        `Class.member` and `member`; and every function parameter.
    """
    names: set[str] = set()
    module: ast.Module = ast.parse(source)
    for node in module.body:
        names.update(defined_names(node))
        if isinstance(node, ast.ClassDef):
            for member in node.body:
                for member_name in defined_names(member):
                    names.update({member_name, f"{node.name}.{member_name}"})
    for node in ast.walk(module):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            names.update(
                argument.arg
                for argument in ast.walk(node.args)
                if isinstance(argument, ast.arg)
            )
    return names


def defined_names(node: ast.stmt) -> set[str]:
    """Name what one statement defines, if anything.

    Args:
        node: A statement in a module or class body.

    Returns:
        The class, function or assigned names.
    """
    if isinstance(node, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
        return {node.name}
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return {node.target.id}
    if isinstance(node, ast.Assign):
        return {target.id for target in node.targets if isinstance(target, ast.Name)}
    return set()


def backend_names(package: Path) -> set[str]:
    """Collect every name the back end defines, and its files.

    Args:
        package: The back end's package folder.

    Returns:
        The names from every module, plus each file's path from the package and its
        file name, such as "ai/providers/claude.py" and "claude.py".
    """
    names: set[str] = set()
    for path in package.rglob("*.py"):
        names.update(python_names(path.read_text(encoding="utf-8")))
        names.update({path.relative_to(package).as_posix(), path.name})
    return names


def frontend_names(source_folder: Path, api_types: Path) -> set[str]:
    """Collect every name the front end exports, its files, and the API's fields.

    Args:
        source_folder: The front end's `src` folder.
        api_types: The generated API types, `schema.d.ts`.

    Returns:
        Each file's name without its extension, each exported name, and each field
        name in the API types.
    """
    names: set[str] = set(API_FIELD.findall(api_types.read_text(encoding="utf-8")))
    for path in [*source_folder.rglob("*.ts"), *source_folder.rglob("*.tsx")]:
        names.add(path.name.split(".")[0])
        names.update(FRONTEND_EXPORT.findall(path.read_text(encoding="utf-8")))
    return names


def unknown_names(glossary_names: Iterable[str], known_names: set[str]) -> list[str]:
    """Find the glossary's names that the code doesn't have.

    Args:
        glossary_names: The names one glossary column gives.
        known_names: The names the code defines.

    Returns:
        The names not found, sorted.
    """
    return sorted(set(glossary_names) - known_names)


def test_the_glossary_has_names_in_both_columns() -> None:
    """Both columns are read, so a change to the glossary's layout can't empty it."""
    glossary: str = GLOSSARY_PATH.read_text(encoding="utf-8")

    assert {"Take5", "Hazard.covers", "fix.py"} <= glossary_code_names(
        glossary,
        BACKEND_COLUMN,
    )
    assert {"Take5Form", "useTake5Draft", "worker_name"} <= glossary_code_names(
        glossary,
        FRONTEND_COLUMN,
    )


def test_every_back_end_name_in_the_glossary_is_in_the_code() -> None:
    """A renamed class, field or function makes the glossary's back-end column fail."""
    glossary: str = GLOSSARY_PATH.read_text(encoding="utf-8")

    missing: list[str] = unknown_names(
        glossary_code_names(glossary, BACKEND_COLUMN),
        backend_names(BACKEND_PACKAGE),
    )

    assert not missing, f"Back-end names in docs/glossary.md the code lacks: {missing}"


def test_every_front_end_name_in_the_glossary_is_in_the_code() -> None:
    """A renamed component, hook or API field makes the front-end column fail."""
    glossary: str = GLOSSARY_PATH.read_text(encoding="utf-8")

    missing: list[str] = unknown_names(
        glossary_code_names(glossary, FRONTEND_COLUMN),
        frontend_names(FRONTEND_SOURCE, API_TYPES_PATH),
    )

    assert not missing, f"Front-end names in docs/glossary.md the code lacks: {missing}"


def test_a_class_member_is_found_with_and_without_its_class() -> None:
    """`Hazard.covers` and `covers` are both names; `Hazard.missing` is not."""
    source: str = (
        "class Hazard:\n"
        "    covers: tuple[str, ...] = ()\n"
        "    def rating(self) -> int:\n"
        "        return 1\n"
        "def submit(draft: object, submission_id: str) -> None:\n"
        "    pass\n"
    )

    names: set[str] = python_names(source)

    assert {"Hazard", "Hazard.covers", "covers", "Hazard.rating", "submit"} <= names
    assert "submission_id" in names
    assert unknown_names(["Hazard.covers", "Hazard.missing"], names) == [
        "Hazard.missing",
    ]


def test_only_code_names_in_the_named_column_are_read() -> None:
    """Words not written as code, the header and other columns are left out."""
    glossary: str = (
        "| Term | Meaning | Back end | Front end | Rules |\n"
        "| --- | --- | --- | --- | --- |\n"
        "| Hazard | Uses `NotThis` | `Hazard`; saved as `SavedTake5` | none | T1 |\n"
    )

    assert glossary_code_names(glossary, BACKEND_COLUMN) == {"Hazard", "SavedTake5"}
    assert glossary_code_names(glossary, FRONTEND_COLUMN) == set()
