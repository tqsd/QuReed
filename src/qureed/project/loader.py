from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from qureed.project.models import ProjectConfig, QureedProject

PROJECT_FILE = "qureed.toml"


class ProjectConfigError(RuntimeError):
    pass


class ProjectNotFoundError(ProjectConfigError):
    pass


def find_project_file(start: Path | None = None) -> Path | None:
    current = (start or Path.cwd()).resolve()
    for directory in (current, *current.parents):
        candidate = directory / PROJECT_FILE
        if candidate.exists():
            return candidate
    return None


def load_project(start: Path | None = None) -> QureedProject:
    project_file = find_project_file(start)
    if project_file is None:
        raise ProjectNotFoundError(
            "No qureed.toml found; run 'qureed project init' first"
        )
    return load_project_file(project_file)


def load_optional_project(start: Path | None = None) -> QureedProject | None:
    project_file = find_project_file(start)
    if project_file is None:
        return None
    return load_project_file(project_file)


def load_project_file(project_file: Path) -> QureedProject:
    project_file = project_file.resolve()
    with project_file.open("rb") as handle:
        data: dict[str, Any] = tomllib.load(handle)

    root = project_file.parent
    config = parse_project_config(data, root)
    return QureedProject(
        root=root,
        config_path=project_file,
        config=config,
        custom_device_paths=resolve_paths(
            root, config.custom_device_paths, "custom device paths"
        ),
        spec_output_path=resolve_path(
            root, config.spec_output_path, "spec output path"
        ),
        diagrams_path=resolve_path(
            root, config.diagrams_path, "diagrams path"
        ),
        scripts_path=resolve_path(root, config.scripts_path, "scripts path"),
    )


def parse_project_config(data: dict[str, Any], root: Path) -> ProjectConfig:
    project_data = require_table(data, "project")
    paths_data = data.get("paths", {})
    devices_data = data.get("devices", {})

    if not isinstance(paths_data, dict):
        raise ProjectConfigError("[paths] must be a TOML table")
    if not isinstance(devices_data, dict):
        raise ProjectConfigError("[devices] must be a TOML table")

    return ProjectConfig(
        name=read_string(
            project_data,
            "name",
            default=root.name,
            section="project",
        ),
        custom_device_paths=read_string_tuple(
            paths_data,
            "custom_devices",
            default=("devices",),
            section="paths",
        ),
        device_class_paths=read_string_tuple(
            devices_data,
            "class_paths",
            default=(),
            section="devices",
        ),
        spec_output_path=read_string(
            paths_data,
            "specs",
            default="specs/devices",
            section="paths",
        ),
        diagrams_path=read_string(
            paths_data,
            "diagrams",
            default="diagrams",
            section="paths",
        ),
        scripts_path=read_string(
            paths_data,
            "scripts",
            default="scripts",
            section="paths",
        ),
    )


def require_table(data: dict[str, Any], name: str) -> dict[str, Any]:
    value = data.get(name)
    if value is None:
        raise ProjectConfigError(f"Missing required [{name}] table")
    if not isinstance(value, dict):
        raise ProjectConfigError(f"[{name}] must be a TOML table")
    return value


def read_string(
    data: dict[str, Any],
    key: str,
    *,
    default: str,
    section: str,
) -> str:
    value = data.get(key, default)
    if not isinstance(value, str):
        raise ProjectConfigError(f"[{section}].{key} must be a string")
    if not value:
        raise ProjectConfigError(f"[{section}].{key} cannot be empty")
    return value


def read_string_tuple(
    data: dict[str, Any],
    key: str,
    *,
    default: tuple[str, ...],
    section: str,
) -> tuple[str, ...]:
    value = data.get(key, list(default))
    if not isinstance(value, list):
        raise ProjectConfigError(f"[{section}].{key} must be a list")
    if not all(isinstance(item, str) and item for item in value):
        raise ProjectConfigError(
            f"[{section}].{key} must contain only non-empty strings"
        )
    return tuple(value)


def resolve_paths(
    root: Path, paths: tuple[str, ...], label: str
) -> tuple[Path, ...]:
    return tuple(resolve_path(root, path, label) for path in paths)


def resolve_path(root: Path, path: str, label: str) -> Path:
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = root / candidate
    try:
        return candidate.resolve()
    except RuntimeError as exc:
        raise ProjectConfigError(f"Could not resolve {label}: {path}") from exc
