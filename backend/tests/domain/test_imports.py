"""Check that domain rules stay independent of web, storage and outside services."""

import ast
import sys
from importlib.util import resolve_name
from pathlib import Path

import pytest

_DOMAIN_ROOT: Path = Path(__file__).parents[2] / "src/risk_assessment/domain"


@pytest.mark.parametrize("module_path", sorted(_DOMAIN_ROOT.rglob("*.py")))
def test_domain_imports_follow_the_architecture(module_path: Path) -> None:
    """Allow standard library, pydantic and inward imports between domain modules."""
    package: str = "risk_assessment.domain"
    relative_parent: tuple[str, ...] = module_path.relative_to(
        _DOMAIN_ROOT
    ).parent.parts
    if relative_parent:
        package += "." + ".".join(relative_parent)
    imports: list[str] = []
    for node in ast.walk(ast.parse(module_path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            source: str = resolve_name("." * node.level + (node.module or ""), package)
            imports.extend(f"{source}.{alias.name}" for alias in node.names)
    for imported in imports:
        root: str = imported.split(".")[0]
        if root == "risk_assessment":
            assert imported.startswith("risk_assessment.domain."), module_path
            if module_path.parent == _DOMAIN_ROOT:
                assert not imported.startswith("risk_assessment.domain.take5"), (
                    module_path
                )
        else:
            assert root in sys.stdlib_module_names or root == "pydantic", module_path
