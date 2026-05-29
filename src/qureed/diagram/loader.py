from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qureed.diagram.models import Diagram


class DiagramError(RuntimeError):
    pass


def create_empty_diagram() -> Diagram:
    return Diagram()


def load_diagram(path: Path) -> Diagram:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise DiagramError(f"{path}: invalid JSON: {exc}") from exc

    validate_diagram_structure(data, path)
    return Diagram.from_dict(data)


def save_diagram(diagram: Diagram, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(diagram.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def validate_diagram_structure(data: Any, path: Path | None = None) -> None:
    label = f"{path}: " if path is not None else ""
    if not isinstance(data, dict):
        raise DiagramError(f"{label}diagram must be a JSON object")

    version = data.get("version", 1)
    if not isinstance(version, int):
        raise DiagramError(f"{label}version must be an integer")

    devices = data.get("devices", [])
    if not isinstance(devices, list):
        raise DiagramError(f"{label}devices must be a list")
    for index, device in enumerate(devices):
        validate_device_structure(device, f"{label}devices[{index}]")

    connections = data.get("connections", [])
    if not isinstance(connections, list):
        raise DiagramError(f"{label}connections must be a list")
    for index, connection in enumerate(connections):
        validate_connection_structure(
            connection, f"{label}connections[{index}]"
        )


def validate_device_structure(data: Any, label: str) -> None:
    if not isinstance(data, dict):
        raise DiagramError(f"{label} must be an object")
    require_string(data, "id", label)
    require_string(data, "type", label)

    position = data.get("position", {})
    if not isinstance(position, dict):
        raise DiagramError(f"{label}.position must be an object")
    for key in ("x", "y"):
        value = position.get(key, 0)
        if not isinstance(value, (int, float)):
            raise DiagramError(f"{label}.position.{key} must be numeric")

    properties = data.get("properties", {})
    if not isinstance(properties, dict):
        raise DiagramError(f"{label}.properties must be an object")


def validate_connection_structure(data: Any, label: str) -> None:
    if not isinstance(data, dict):
        raise DiagramError(f"{label} must be an object")
    if "id" in data and not isinstance(data["id"], str):
        raise DiagramError(f"{label}.id must be a string")
    validate_endpoint(data.get("source"), f"{label}.source")
    validate_endpoint(data.get("target"), f"{label}.target")


def validate_endpoint(data: Any, label: str) -> None:
    if not isinstance(data, dict):
        raise DiagramError(f"{label} must be an object")
    require_string(data, "device", label)
    require_string(data, "port", label)


def require_string(data: dict[str, Any], key: str, label: str) -> None:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise DiagramError(f"{label}.{key} must be a non-empty string")
