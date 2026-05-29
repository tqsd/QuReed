from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from qureed.diagram.models import Diagram, DiagramConnection
from qureed.project import QureedProject


@dataclass(frozen=True)
class DiagramValidationResult:
    errors: tuple[str, ...]

    @property
    def valid(self) -> bool:
        return not self.errors


def validate_diagram(
    diagram: Diagram, project: QureedProject
) -> DiagramValidationResult:
    specs = load_device_specs(project.spec_output_path)
    errors: list[str] = []
    device_ids: set[str] = set()

    for device in diagram.devices:
        if device.id in device_ids:
            errors.append(f"Duplicate device id: {device.id}")
        device_ids.add(device.id)

        spec = specs.get(device.type)
        if spec is None:
            errors.append(
                f"Device {device.id} references unknown type {device.type}"
            )
            continue
        errors.extend(
            validate_device_properties(device.id, device.properties, spec)
        )

    devices_by_id = {device.id: device for device in diagram.devices}
    for index, connection in enumerate(diagram.connections):
        errors.extend(
            validate_connection(index, connection, devices_by_id, specs)
        )

    return DiagramValidationResult(errors=tuple(errors))


def load_device_specs(spec_dir: Path) -> dict[str, dict[str, Any]]:
    specs: dict[str, dict[str, Any]] = {}
    if not spec_dir.exists():
        return specs

    for path in sorted(spec_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            class_path = data.get("class_path")
            if isinstance(class_path, str):
                specs[class_path] = data
            spec_id = data.get("id")
            if isinstance(spec_id, str):
                specs[spec_id] = data
    return specs


def validate_device_properties(
    device_id: str, properties: dict[str, Any], spec: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    spec_properties = spec.get("properties", {})
    if not isinstance(spec_properties, dict):
        return errors

    for name in properties:
        if name not in spec_properties:
            errors.append(f"Device {device_id} has unknown property {name}")

    for name, metadata in spec_properties.items():
        if not isinstance(metadata, dict):
            continue
        has_default = "default" in metadata and metadata["default"] is not None
        if not has_default and name not in properties:
            errors.append(f"Device {device_id} is missing property {name}")

    return errors


def validate_connection(
    index: int,
    connection: DiagramConnection,
    devices_by_id: dict[str, Any],
    specs: dict[str, dict[str, Any]],
) -> list[str]:
    errors: list[str] = []
    label = connection.id or f"connection[{index}]"

    source_device = devices_by_id.get(connection.source_device)
    target_device = devices_by_id.get(connection.target_device)
    if source_device is None:
        errors.append(
            f"{label} references unknown source device "
            f"{connection.source_device}"
        )
    if target_device is None:
        errors.append(
            f"{label} references unknown target device "
            f"{connection.target_device}"
        )
    if source_device is None or target_device is None:
        return errors

    source_spec = specs.get(source_device.type)
    target_spec = specs.get(target_device.type)
    if source_spec is None or target_spec is None:
        return errors

    source_port = read_port(source_spec, connection.source_port)
    target_port = read_port(target_spec, connection.target_port)
    if source_port is None:
        errors.append(
            f"{label} references unknown source port "
            f"{connection.source_device}.{connection.source_port}"
        )
    if target_port is None:
        errors.append(
            f"{label} references unknown target port "
            f"{connection.target_device}.{connection.target_port}"
        )
    if source_port is None or target_port is None:
        return errors

    errors.extend(validate_direction(label, source_port, target_port))
    errors.extend(validate_signal_type(label, source_port, target_port))
    return errors


def read_port(spec: dict[str, Any], port_name: str) -> dict[str, Any] | None:
    ports = spec.get("ports", {})
    if not isinstance(ports, dict):
        return None
    port = ports.get(port_name)
    return port if isinstance(port, dict) else None


def validate_direction(
    label: str, source_port: dict[str, Any], target_port: dict[str, Any]
) -> list[str]:
    source_direction = source_port.get("direction")
    target_direction = target_port.get("direction")
    if source_direction is None or target_direction is None:
        return []
    if source_direction != "output" or target_direction != "input":
        return [
            f"{label} must connect output to input; got "
            f"{source_direction} to {target_direction}"
        ]
    return []


def validate_signal_type(
    label: str, source_port: dict[str, Any], target_port: dict[str, Any]
) -> list[str]:
    source_signal_type = source_port.get("signal_type")
    target_signal_type = target_port.get("signal_type")
    if not source_signal_type or not target_signal_type:
        return []
    if source_signal_type != target_signal_type:
        return [
            f"{label} signal type mismatch: "
            f"{source_signal_type} to {target_signal_type}"
        ]
    return []
