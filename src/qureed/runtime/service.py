from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qureed.diagram import create_empty_diagram
from qureed.diagram import load_diagram as load_diagram_file
from qureed.diagram import save_diagram
from qureed.diagram import validate_diagram as validate_loaded_diagram
from qureed.project import QureedProject
from qureed.project import load_project as load_project_config
from qureed.registry import build_registry, describe_device
from qureed.scriptgen import default_script_output_path
from qureed.scriptgen import generate_script_from_file
from qureed.specs import generate_device_specs, validate_device_specs
from qureed.runtime.models import (
    RuntimeDevice,
    RuntimeDeviceDetails,
    RuntimeDiagram,
    RuntimeScript,
    RuntimeSpec,
    RuntimeSpecGeneration,
    RuntimeValidation,
)


class RuntimeService:
    def __init__(self, project: QureedProject):
        self.project = project

    @classmethod
    def load_project(cls, project_root: str | Path | None = None):
        start = Path(project_root) if project_root is not None else None
        return cls(load_project_config(start))

    def load_diagram(self, path: str | Path) -> RuntimeDiagram:
        resolved = self.resolve_diagram_path(path)
        return RuntimeDiagram(
            path=resolved, diagram=load_diagram_file(resolved)
        )

    def create_diagram(self, path: str | Path) -> RuntimeDiagram:
        resolved = self.resolve_diagram_path(path)
        diagram = create_empty_diagram()
        save_diagram(diagram, resolved)
        return RuntimeDiagram(path=resolved, diagram=diagram)

    def validate_diagram(self, path: str | Path) -> RuntimeValidation:
        runtime_diagram = self.load_diagram(path)
        result = validate_loaded_diagram(runtime_diagram.diagram, self.project)
        return RuntimeValidation(valid=result.valid, errors=result.errors)

    def generate_script(
        self,
        path: str | Path,
        output_path: str | Path | None = None,
    ) -> RuntimeScript:
        diagram_path = self.resolve_diagram_path(path)
        resolved_output = self.resolve_script_output_path(
            diagram_path, output_path
        )
        result = generate_script_from_file(
            diagram_path, self.project, resolved_output
        )
        return RuntimeScript(path=result.output_path, content=result.script)

    def list_available_devices(self) -> tuple[RuntimeDevice, ...]:
        records = build_registry(self.project).all()
        return tuple(
            RuntimeDevice(
                id=record.id,
                source=record.source,
                category=record.category,
                name=record.display_name,
                class_path=record.class_path,
            )
            for record in records
        )

    def inspect_device(self, identifier: str) -> RuntimeDeviceDetails:
        record = build_registry(self.project).find(identifier)
        data = describe_device(record)
        return RuntimeDeviceDetails(
            id=data["id"],
            source=data["source"],
            class_path=data["class_path"],
            display_name=data["display_name"],
            category=data["category"],
            properties=tuple(data["properties"]),
            ports=tuple(data["ports"]),
            doc=data["doc"],
            warnings=tuple(data["warnings"]),
        )

    def list_available_specs(self) -> tuple[RuntimeSpec, ...]:
        specs: list[RuntimeSpec] = []
        for path in sorted(self.project.spec_output_path.glob("*.json")):
            specs.append(read_runtime_spec(path))
        return tuple(specs)

    def generate_specs(self) -> RuntimeSpecGeneration:
        result = generate_device_specs(
            build_registry(self.project), self.project
        )
        return RuntimeSpecGeneration(
            output_dir=result.output_dir,
            written=result.written,
            warnings=result.warnings,
        )

    def validate_specs(self) -> RuntimeValidation:
        result = validate_device_specs(self.project)
        return RuntimeValidation(valid=result.valid, errors=result.errors)

    def resolve_diagram_path(self, path: str | Path) -> Path:
        candidate = Path(path).expanduser()
        if candidate.is_absolute():
            return candidate
        return (self.project.diagrams_path / candidate).resolve()

    def resolve_script_output_path(
        self,
        diagram_path: Path,
        output_path: str | Path | None,
    ) -> Path:
        if output_path is None:
            return default_script_output_path(
                self.project, diagram_path
            ).resolve()

        candidate = Path(output_path).expanduser()
        if candidate.is_absolute():
            return candidate
        return (self.project.scripts_path / candidate).resolve()


def read_runtime_spec(path: Path) -> RuntimeSpec:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return RuntimeSpec(
            class_path=path.stem,
            source="invalid",
            category="",
            path=path,
            valid=False,
        )
    if not isinstance(data, dict):
        return RuntimeSpec(
            class_path=path.stem,
            source="invalid",
            category="",
            path=path,
            valid=False,
        )
    return RuntimeSpec(
        class_path=read_string(data, "class_path", path.stem),
        source=read_string(data, "source", ""),
        category=read_string(data, "category", ""),
        path=path,
        valid=True,
    )


def read_string(data: dict[str, Any], key: str, default: str) -> str:
    value = data.get(key, default)
    return value if isinstance(value, str) else default


def load_project(project_root: str | Path | None = None) -> RuntimeService:
    return RuntimeService.load_project(project_root)


def load_diagram(path: str | Path) -> RuntimeDiagram:
    return load_project().load_diagram(path)


def validate_diagram(path: str | Path) -> RuntimeValidation:
    return load_project().validate_diagram(path)


def generate_script(path: str | Path) -> RuntimeScript:
    return load_project().generate_script(path)


def list_available_devices() -> tuple[RuntimeDevice, ...]:
    return load_project().list_available_devices()


def inspect_device(identifier: str) -> RuntimeDeviceDetails:
    return load_project().inspect_device(identifier)


def list_available_specs() -> tuple[RuntimeSpec, ...]:
    return load_project().list_available_specs()


def generate_specs() -> RuntimeSpecGeneration:
    return load_project().generate_specs()


def validate_specs() -> RuntimeValidation:
    return load_project().validate_specs()
