from __future__ import annotations

import inspect
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from qureed.device_registry import (
    DeviceRecord,
    DeviceRegistry,
    read_property_without_instance,
    try_import_class,
)
from qureed.project import QureedProject


DEVICE_SPEC_DIR = Path("specs") / "devices"
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
class SpecGenerationResult:
    output_dir: Path
    written: tuple[Path, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class SpecValidationResult:
    checked: tuple[Path, ...]
    errors: tuple[str, ...]

    @property
    def valid(self) -> bool:
        return not self.errors


def generate_device_specs(
    registry: DeviceRegistry, project: QureedProject
) -> SpecGenerationResult:
    output_dir = project.root / DEVICE_SPEC_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    warnings: list[str] = []
    for record in registry.all():
        spec = build_device_spec(record)
        path = output_dir / deterministic_spec_filename(record)
        path.write_text(
            json.dumps(spec, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        written.append(path)
        warnings.extend(
            f"{record.class_path}: {warning}"
            for warning in spec.get("warnings", [])
        )

    return SpecGenerationResult(
        output_dir=output_dir,
        written=tuple(sorted(written)),
        warnings=tuple(warnings),
    )


def validate_device_specs(project: QureedProject) -> SpecValidationResult:
    spec_dir = project.root / DEVICE_SPEC_DIR
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


def build_device_spec(record: DeviceRecord) -> dict[str, Any]:
    module, class_name = split_class_path(record.class_path)
    warnings: list[str] = []
    if record.import_error:
        warnings.append(
            f"Could not import device class: {record.import_error}"
        )

    device_class = record.device_class
    if device_class is None and not record.import_error:
        device_class, import_error = try_import_class(record.class_path)
        if import_error:
            warnings.append(f"Could not import device class: {import_error}")

    return {
        "id": record.class_path,
        "class_path": record.class_path,
        "module": module,
        "class_name": class_name,
        "source": record.source,
        "gui_name": read_gui_name(record, device_class),
        "category": record.category,
        "icon": read_icon(device_class, warnings),
        "properties": read_properties(device_class, warnings),
        "ports": read_ports(device_class, warnings),
        "doc": read_doc(device_class),
        "warnings": warnings,
    }


def split_class_path(class_path: str) -> tuple[str, str]:
    module, _, class_name = class_path.rpartition(".")
    return module, class_name


def deterministic_spec_filename(record: DeviceRecord) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]+", "_", record.class_path).strip("_")
    return f"{record.source}__{normalized.lower()}.json"


def read_gui_name(record: DeviceRecord, device_class: type | None) -> str:
    if device_class is None:
        return record.display_name

    value = read_property_without_instance(device_class, "gui_name")
    return value if isinstance(value, str) else record.display_name


def read_icon(device_class: type | None, warnings: list[str]) -> str | None:
    if device_class is None:
        return None

    try:
        value = read_property_without_instance(device_class, "gui_icon")
    except Exception as exc:
        warnings.append(
            f"Could not inspect gui_icon: {type(exc).__name__}: {exc}"
        )
        return None

    return value if isinstance(value, str) else None


def read_properties(
    device_class: type | None, warnings: list[str]
) -> dict[str, dict[str, Any]]:
    if device_class is None:
        return {}

    try:
        raw_properties = getattr(device_class, "properties", {})
    except Exception as exc:
        warnings.append(
            f"Could not inspect properties: {type(exc).__name__}: {exc}"
        )
        return {}

    properties: dict[str, dict[str, Any]] = {}
    if not isinstance(raw_properties, dict):
        warnings.append("Device properties metadata is not a dictionary")
        return properties

    for name in sorted(raw_properties):
        metadata = raw_properties[name]
        if not isinstance(metadata, dict):
            warnings.append(f"Property {name} metadata is not a dictionary")
            continue

        value_type = metadata.get("type")
        properties[name] = {
            "type": type_name(value_type),
            "default": json_safe(metadata.get("value")),
        }

    return properties


def read_ports(
    device_class: type | None, warnings: list[str]
) -> dict[str, dict[str, Any]]:
    if device_class is None:
        return {}

    try:
        raw_ports = getattr(device_class, "port_definitions", {})
    except Exception as exc:
        warnings.append(
            f"Could not inspect ports: {type(exc).__name__}: {exc}"
        )
        return {}

    ports: dict[str, dict[str, Any]] = {}
    if not isinstance(raw_ports, dict):
        warnings.append("Device port_definitions metadata is not a dictionary")
        return ports

    for name in sorted(raw_ports):
        port = raw_ports[name]
        signal_type = getattr(port, "signal_type", None)
        ports[name] = {
            "direction": getattr(port, "direction", None),
            "signal_type": type_name(signal_type),
        }

    return ports


def read_doc(device_class: type | None) -> dict[str, str]:
    if device_class is None:
        return {"summary": ""}

    doc = inspect.getdoc(device_class) or ""
    summary = doc.splitlines()[0] if doc else ""
    return {"summary": summary}


def type_name(value: Any) -> str | None:
    if inspect.isclass(value):
        return value.__name__
    if value is None:
        return None
    if hasattr(value, "__name__"):
        return str(value.__name__)
    return str(value)


def json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if isinstance(value, dict):
        return {
            str(key): json_safe(item)
            for key, item in sorted(
                value.items(), key=lambda entry: str(entry[0])
            )
        }
    return repr(value)
