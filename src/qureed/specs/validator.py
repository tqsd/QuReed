from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from qureed.project import QureedProject

REQUIRED_DEVICE_SPEC_KEYS = {
    "id",
    "class_path",
    "module",
    "class_name",
    "source",
    "gui_name",
    "category",
    "icon",
    "properties",
    "ports",
    "doc",
    "warnings",
}


@dataclass(frozen=True)
class SpecValidationResult:
    checked: tuple[Path, ...]
    errors: tuple[str, ...]

    @property
    def valid(self) -> bool:
        return not self.errors


def validate_device_specs(project: QureedProject) -> SpecValidationResult:
    spec_dir = project.spec_output_path
    errors: list[str] = []
    checked: list[Path] = []

    if not spec_dir.exists():
        return SpecValidationResult(
            checked=(),
            errors=(f"{spec_dir} does not exist",),
        )

    for path in sorted(spec_dir.glob("*.json")):
        checked.append(path)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{path}: invalid JSON: {exc}")
            continue

        errors.extend(validate_device_spec(data, path))

    if not checked:
        errors.append(f"{spec_dir} contains no device spec JSON files")

    return SpecValidationResult(checked=tuple(checked), errors=tuple(errors))


def validate_device_spec(data: Any, path: Path) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return [f"{path}: expected a JSON object"]

    missing = sorted(REQUIRED_DEVICE_SPEC_KEYS.difference(data))
    if missing:
        errors.append(f"{path}: missing keys: {', '.join(missing)}")

    for key in ("id", "class_path", "module", "class_name", "source"):
        if key in data and not isinstance(data[key], str):
            errors.append(f"{path}: {key} must be a string")

    if data.get("source") not in {"builtin", "project"}:
        errors.append(f"{path}: source must be 'builtin' or 'project'")

    for key in ("properties", "ports", "doc"):
        if key in data and not isinstance(data[key], dict):
            errors.append(f"{path}: {key} must be an object")

    if "warnings" in data and not isinstance(data["warnings"], list):
        errors.append(f"{path}: warnings must be a list")

    return errors
