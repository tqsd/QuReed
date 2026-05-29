from __future__ import annotations

import ast
from pathlib import Path


INTERFACE_PACKAGES = {
    "cli",
    "diagram",
    "gui",
    "interface",
    "project",
    "registry",
    "runtime",
    "scriptgen",
    "server",
    "specs",
}
FORBIDDEN_IMPORTS = {
    "qureed.cli",
    "qureed.diagram",
    "qureed.interface",
    "qureed.project",
    "qureed.registry",
    "qureed.runtime",
    "qureed.scriptgen",
    "qureed.specs",
    "qureed.gui",
    "qureed.server",
    "qureed.web",
    "qureed.gui_server",
    "frontend",
}
SERVER_FORBIDDEN_DIRECT_IMPORTS = {
    "qureed.devices",
    "qureed.interface.registry",
    "qureed.interface.specs",
    "qureed.registry",
    "qureed.specs",
}
FRONTEND_FORBIDDEN_STRINGS = {
    "from qureed",
    "import qureed",
    "qureed.interface",
    "qureed.devices",
    "qureed.simulation",
    "qureed.signals",
}


def test_core_modules_do_not_import_interface_layers() -> None:
    violations: list[str] = []
    for path in core_python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for import_name in imported_modules(tree):
            if is_forbidden_import(import_name):
                violations.append(f"{path}: imports {import_name}")

    assert violations == []


def test_frontend_source_stays_outside_python_package() -> None:
    assert not (Path("src") / "qureed" / "frontend").exists()


def test_frontend_does_not_reference_python_internals() -> None:
    violations: list[str] = []
    for path in frontend_source_files():
        text = path.read_text(encoding="utf-8")
        for forbidden in FRONTEND_FORBIDDEN_STRINGS:
            if forbidden in text:
                violations.append(f"{path}: references {forbidden}")

    assert violations == []


def test_server_does_not_inspect_devices_directly() -> None:
    violations: list[str] = []
    for path in interface_python_files("server"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for import_name in imported_modules(tree):
            if is_server_forbidden_import(import_name):
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


def interface_python_files(package: str) -> list[Path]:
    root = Path("src") / "qureed" / package
    return sorted(root.rglob("*.py"))


def frontend_source_files() -> list[Path]:
    root = Path("frontend")
    if not root.exists():
        return []
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix in {".svelte", ".ts", ".js", ".json", ".html"}
    )


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


def is_server_forbidden_import(import_name: str) -> bool:
    return any(
        import_name == forbidden or import_name.startswith(f"{forbidden}.")
        for forbidden in SERVER_FORBIDDEN_DIRECT_IMPORTS
    )
