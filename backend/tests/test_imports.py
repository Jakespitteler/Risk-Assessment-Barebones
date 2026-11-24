"""Check that each package imports only what docs/architecture.md allows.

The rules are under "Boundaries" in docs/architecture.md.
"""

import ast
import sys
from importlib.util import resolve_name
from pathlib import Path

import pytest

_PACKAGE_ROOT: Path = Path(__file__).parents[1] / "src/risk_assessment"

# What each package may import from the app, besides itself.
_ALLOWED: dict[str, tuple[str, ...]] = {
    "domain": (),
    "services": ("risk_assessment.domain",),
    "storage": ("risk_assessment.services.ports", "risk_assessment.domain"),
    "ai": ("risk_assessment.services.ports", "risk_assessment.domain"),
    "api": ("risk_assessment.services", "risk_assessment.domain"),
}

# The composition root may also plug in storage, the AI and settings.
_COMPOSITION_ROOT: Path = _PACKAGE_ROOT / "api/app.py"
_COMPOSITION_ROOT_ALSO: tuple[str, ...] = (
    "risk_assessment.storage",
    "risk_assessment.ai",
    "risk_assessment.settings",
)

# An AI provider's adapter knows nothing of the app but the model Protocol.
_PROVIDERS: Path = _PACKAGE_ROOT / "ai/providers"
_PROVIDERS_MAY_IMPORT: tuple[str, ...] = ("risk_assessment.ai.model",)

# Outside the app, only these may be imported, besides the standard library.
_OUTSIDE: dict[str, tuple[str, ...]] = {
    "domain": ("pydantic",),
    "services": ("pydantic",),
    "storage": ("pydantic",),
    # Each provider's library; httpx2, which both use, types ChatGPT's test client.
    "ai": ("pydantic", "anthropic", "openai", "httpx2"),
    "api": ("pydantic", "fastapi", "starlette"),
}


def _modules() -> list[Path]:
    """Every module in a package that has rules.

    Returns:
        The modules' paths, sorted.
    """
    return sorted(
        path for package in _ALLOWED for path in (_PACKAGE_ROOT / package).rglob("*.py")
    )


def _imports(module_path: Path) -> list[str]:
    """List the full name of everything a module imports.

    Args:
        module_path: The module's file.

    Returns:
        Each imported name, such as `risk_assessment.domain.risk.rate`.
    """
    package: str = ".".join(
        ("risk_assessment", *module_path.relative_to(_PACKAGE_ROOT).parent.parts),
    )
    imports: list[str] = []
    for node in ast.walk(ast.parse(module_path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            source: str = resolve_name("." * node.level + (node.module or ""), package)
            imports.extend(f"{source}.{alias.name}" for alias in node.names)
    return imports


def _is_within(name: str, prefixes: tuple[str, ...]) -> bool:
    """Say whether a dotted name is one of the prefixes or inside one.

    Args:
        name: A dotted name.
        prefixes: Dotted package or module names.

    Returns:
        True if the name starts with any of the prefixes.
    """
    return any(name == prefix or name.startswith(prefix + ".") for prefix in prefixes)


@pytest.mark.parametrize(
    "module_path",
    _modules(),
    ids=lambda path: str(path.relative_to(_PACKAGE_ROOT)),
)
def test_imports_follow_the_architecture(module_path: Path) -> None:
    """Each module imports only its own package, what it may use, and libraries."""
    package: str = module_path.relative_to(_PACKAGE_ROOT).parts[0]
    allowed: tuple[str, ...] = (f"risk_assessment.{package}", *_ALLOWED[package])
    if module_path == _COMPOSITION_ROOT:
        allowed += _COMPOSITION_ROOT_ALSO
    for imported in _imports(module_path):
        if imported.split(".")[0] == "risk_assessment":
            assert _is_within(imported, allowed), f"{module_path}: {imported}"
        else:
            root: str = imported.split(".")[0]
            assert root in sys.stdlib_module_names or root in _OUTSIDE[package], (
                f"{module_path}: {imported}"
            )


@pytest.mark.parametrize("module_path", sorted(_PACKAGE_ROOT.glob("domain/*.py")))
def test_shared_domain_files_know_nothing_about_a_take5(module_path: Path) -> None:
    """The files directly under `domain/` never import `domain/take5`."""
    for imported in _imports(module_path):
        assert not imported.startswith("risk_assessment.domain.take5"), module_path


@pytest.mark.parametrize(
    "module_path",
    sorted(_PROVIDERS.glob("*.py")),
    ids=lambda path: path.name,
)
def test_ai_providers_import_nothing_from_the_app_but_the_model(
    module_path: Path,
) -> None:
    """Each adapter in `ai/providers/` imports only `ai/model.py` from the app."""
    for imported in _imports(module_path):
        if imported.split(".")[0] == "risk_assessment":
            assert _is_within(imported, _PROVIDERS_MAY_IMPORT), (
                f"{module_path}: {imported}"
            )
