from __future__ import annotations

import os
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_FILE = "qureed.toml"
PROJECT_DEVICE_DIR = "devices"
PROJECT_SPEC_DEVICE_DIR = Path("specs") / "devices"


@dataclass(frozen=True)
class QureedProject:
    root: Path
    name: str
    device_paths: tuple[str, ...]
    device_class_paths: tuple[str, ...]

    @property
    def path(self) -> Path:
        return self.root / PROJECT_FILE


def default_project_name(path: Path) -> str:
    return path.resolve().name


def find_project_file(start: Path | None = None) -> Path | None:
    current = (start or Path.cwd()).resolve()
    for directory in (current, *current.parents):
        candidate = directory / PROJECT_FILE
        if candidate.exists():
            return candidate
    return None


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
                "[devices]",
                "# Project-local device modules can be added later, e.g.",
                '# class_paths = ["my_devices.custom_source.CustomSource"]',
                "class_paths = []",
                "# paths is reserved for future package/module scanning.",
                f'paths = ["{PROJECT_DEVICE_DIR}"]',
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / PROJECT_DEVICE_DIR).mkdir(exist_ok=True)
    (root / PROJECT_SPEC_DEVICE_DIR).mkdir(parents=True, exist_ok=True)
    return project_file


def load_project(start: Path | None = None) -> QureedProject | None:
    project_file = find_project_file(start)
    if project_file is None:
        return None

    with project_file.open("rb") as handle:
        data: dict[str, Any] = tomllib.load(handle)

    root = project_file.parent
    project_data = data.get("project", {})
    devices_data = data.get("devices", {})
    return QureedProject(
        root=root,
        name=str(project_data.get("name") or default_project_name(root)),
        device_paths=tuple(
            str(item) for item in devices_data.get("paths", ())
        ),
        device_class_paths=tuple(
            str(item) for item in devices_data.get("class_paths", ())
        ),
    )


def add_project_to_import_path(project: QureedProject) -> None:
    root = os.fspath(project.root)
    if root not in sys.path:
        sys.path.insert(0, root)
