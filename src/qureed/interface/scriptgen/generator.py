from __future__ import annotations

import json
import keyword
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from qureed.interface.diagram import Diagram, load_diagram, validate_diagram
from qureed.interface.diagram.validator import load_device_specs
from qureed.interface.project import QureedProject


class ScriptGenerationError(RuntimeError):
    pass


@dataclass(frozen=True)
class ScriptGenerationResult:
    output_path: Path | None
    script: str


def generate_script_from_file(
    diagram_path: Path,
    project: QureedProject,
    output_path: Path | None = None,
) -> ScriptGenerationResult:
    diagram = load_diagram(diagram_path)
    script = generate_script(diagram, project)
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(script, encoding="utf-8")
    return ScriptGenerationResult(output_path=output_path, script=script)


def generate_script(diagram: Diagram, project: QureedProject) -> str:
    validation = validate_diagram(diagram, project)
    if not validation.valid:
        raise ScriptGenerationError(
            "Diagram validation failed:\n"
            + "\n".join(f"- {error}" for error in validation.errors)
        )

    specs = load_device_specs(project.spec_output_path)
    names = variable_names(diagram)
    lines: list[str] = [
        '"""Generated QuReed script from a validated diagram.',
        "",
        "This script instantiates and connects devices only.",
        "Simulation execution is intentionally not started here.",
        '"""',
        "",
    ]
    lines.extend(import_lines(diagram, specs))
    lines.extend(
        [
            "",
            "",
            "def build_experiment():",
            "    # Instantiate devices.",
        ]
    )

    if not diagram.devices:
        lines.append("    devices = {}")
    for device in diagram.devices:
        spec = specs[device.type]
        lines.append(
            f"    {names[device.id]} = {spec['class_name']}()"
        )

    if any(device.properties for device in diagram.devices):
        lines.extend(["", "    # Apply configured properties."])
    for device in diagram.devices:
        variable = names[device.id]
        for name, value in sorted(device.properties.items()):
            lines.append(
                f"    {variable}.set_property("
                f"{name!r}, {python_literal(value)})"
            )

    if diagram.connections:
        lines.extend(
            [
                "",
                "    # Connect devices using GenericDevice.connect().",
            ]
        )
    for connection in diagram.connections:
        source = names[connection.source_device]
        target = names[connection.target_device]
        lines.append(
            f"    {source}.connect("
            f"{source}.Ports[{connection.source_port!r}], "
            f"{target}, "
            f"{target}.Ports[{connection.target_port!r}],"
            ")"
        )

    lines.extend(["", "    return {"])
    for device in sorted(diagram.devices, key=lambda item: item.id):
        lines.append(f"        {device.id!r}: {names[device.id]},")
    lines.extend(["    }", ""])
    return "\n".join(lines) + "\n"


def import_lines(
    diagram: Diagram, specs: dict[str, dict[str, Any]]
) -> list[str]:
    imports = sorted(
        {
            (specs[device.type]["module"], specs[device.type]["class_name"])
            for device in diagram.devices
        }
    )
    return [
        f"from {module} import {class_name}"
        for module, class_name in imports
    ]


def variable_names(diagram: Diagram) -> dict[str, str]:
    used: set[str] = set()
    names: dict[str, str] = {}
    for device in sorted(diagram.devices, key=lambda item: item.id):
        base = sanitize_identifier(device.id)
        candidate = base
        suffix = 2
        while candidate in used:
            candidate = f"{base}_{suffix}"
            suffix += 1
        used.add(candidate)
        names[device.id] = candidate
    return names


def sanitize_identifier(value: str) -> str:
    identifier = re.sub(r"\W+", "_", value).strip("_").lower()
    if not identifier:
        identifier = "device"
    if identifier[0].isdigit():
        identifier = f"device_{identifier}"
    if keyword.iskeyword(identifier):
        identifier = f"{identifier}_device"
    return identifier


def python_literal(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def default_script_output_path(
    project: QureedProject, diagram_path: Path
) -> Path:
    return project.scripts_path / f"{diagram_path.stem}.py"
