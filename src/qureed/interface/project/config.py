from __future__ import annotations

import os
import sys
from pathlib import Path

from qureed.interface.project.loader import (
    PROJECT_FILE,
    find_project_file,
    load_optional_project,
)
from qureed.interface.project.models import QureedProject

PROJECT_DEVICE_DIR = "devices"
PROJECT_SPEC_DEVICE_DIR = Path("specs") / "devices"
PROJECT_DIAGRAMS_DIR = "diagrams"
PROJECT_SCRIPTS_DIR = "scripts"


def default_project_name(path: Path) -> str:
    return path.resolve().name


def create_project(root: Path, name: str | None = None) -> Path:
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    project_file = root / PROJECT_FILE
    if project_file.exists():
        raise FileExistsError(f"{project_file} already exists")

    project_name = name or default_project_name(root)
    project_file.write_text(
        "\n".join(
            [
                "[project]",
                f'name = "{project_name}"',
                "",
                "[paths]",
                f'custom_devices = ["{PROJECT_DEVICE_DIR}"]',
                f'specs = "{PROJECT_SPEC_DEVICE_DIR.as_posix()}"',
                f'diagrams = "{PROJECT_DIAGRAMS_DIR}"',
                f'scripts = "{PROJECT_SCRIPTS_DIR}"',
                "",
                "[devices]",
                "# Project-local device modules can be added later, e.g.",
                '# class_paths = ["my_devices.custom_source.CustomSource"]',
                "class_paths = []",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / PROJECT_DEVICE_DIR).mkdir(exist_ok=True)
    (root / PROJECT_SPEC_DEVICE_DIR).mkdir(parents=True, exist_ok=True)
    (root / PROJECT_DIAGRAMS_DIR).mkdir(exist_ok=True)
    (root / PROJECT_SCRIPTS_DIR).mkdir(exist_ok=True)
    return project_file


def load_project(start: Path | None = None):
    return load_optional_project(start)


def add_project_to_import_path(project: QureedProject) -> None:
    paths = [project.root, *project.custom_device_paths]
    for path in reversed(paths):
        path_string = os.fspath(path)
        if path_string not in sys.path:
            sys.path.insert(0, path_string)
