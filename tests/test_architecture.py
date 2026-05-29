from __future__ import annotations

import ast
from pathlib import Path


INTERFACE_PACKAGES = {
    "cli",
    "diagram",
    "project",
    "registry",
    "runtime",
    "scriptgen",
    "specs",
}
FORBIDDEN_IMPORTS = {
    "qureed.cli",
    "qureed.diagram",
    "qureed.project",
    "qureed.registry",
    "qureed.runtime",
    "qureed.scriptgen",
    "qureed.specs",
    "qureed.gui",
    "qureed.server",
    "qureed.web",
    "qureed.gui_server",
}


def test_core_modules_do_not_import_interface_layers() -> None:
    violations: list[str] = []
    for path in core_python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for import_name in imported_modules(tree):
            if is_forbidden_import(import_name):
                violations.append(f"{path}: imports {import_name}")

    assert violations == []


def core_python_files() -> list[Path]:
    root = Path("src") / "qureed"
    files: list[Path] = []
    for path in root.rglob("*.py"):
        parts = path.relative_to(root).parts
        if "__pycache__" in parts:
            continue
        if parts and parts[0] in INTERFACE_PACKAGES:
            continue
        files.append(path)
    return sorted(files)


def imported_modules(tree: ast.AST) -> list[str]:
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports


def is_forbidden_import(import_name: str) -> bool:
    return any(
        import_name == forbidden or import_name.startswith(f"{forbidden}.")
        for forbidden in FORBIDDEN_IMPORTS
    )
