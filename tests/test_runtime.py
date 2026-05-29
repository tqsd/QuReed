from __future__ import annotations

import json
from pathlib import Path

from qureed.cli.main import main
from qureed.interface.runtime import load_project


def test_runtime_device_listing(tmp_path: Path) -> None:
    project_dir = create_project_with_specs(tmp_path)
    service = load_project(project_dir)

    devices = service.list_available_devices()

    assert any(device.id == "lossy_fiber" for device in devices)
    assert any(device.source == "builtin" for device in devices)


def test_runtime_spec_listing(tmp_path: Path) -> None:
    project_dir = create_project_with_specs(tmp_path)
    service = load_project(project_dir)

    specs = service.list_available_specs()

    assert any(spec.class_path == "test.devices.Source" for spec in specs)
    assert all(spec.valid for spec in specs)


def test_runtime_diagram_validation(tmp_path: Path) -> None:
    project_dir = create_project_with_specs(tmp_path)
    write_valid_diagram(project_dir)
    service = load_project(project_dir)

    result = service.validate_diagram("valid.json")

    assert result.valid
    assert result.errors == ()


def test_runtime_script_generation(tmp_path: Path) -> None:
    project_dir = create_project_with_specs(tmp_path)
    write_valid_diagram(project_dir)
    service = load_project(project_dir)

    result = service.generate_script("valid.json")

    assert result.path == (project_dir / "scripts" / "valid.py").resolve()
    assert result.path.exists()
    assert "from test.devices import Source" in result.content
    assert "src.set_property('rate', 2.5)" in result.content


def create_project_with_specs(tmp_path: Path) -> Path:
    project_dir = tmp_path / "project"
    assert main(["project", "init", str(project_dir), "--no-specs"]) == 0
    spec_dir = project_dir / "specs" / "devices"
    write_spec(
        spec_dir / "source.json",
        class_path="test.devices.Source",
        ports={"out": {"direction": "output", "signal_type": "Pulse"}},
        properties={"rate": {"type": "float", "default": 1.0}},
    )
    write_spec(
        spec_dir / "sink.json",
        class_path="test.devices.Sink",
        ports={"in": {"direction": "input", "signal_type": "Pulse"}},
        properties={"threshold": {"type": "float", "default": 0.0}},
    )
    return project_dir


def write_spec(
    path: Path,
    *,
    class_path: str,
    ports: dict,
    properties: dict,
) -> None:
    path.write_text(
        json.dumps(
            {
                "category": "Test",
                "class_name": class_path.rsplit(".", 1)[-1],
                "class_path": class_path,
                "doc": {"summary": ""},
                "gui_name": class_path,
                "icon": None,
                "id": class_path,
                "module": class_path.rsplit(".", 1)[0],
                "ports": ports,
                "properties": properties,
                "source": "project",
                "warnings": [],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def write_valid_diagram(project_dir: Path) -> Path:
    path = project_dir / "diagrams" / "valid.json"
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "devices": [
                    {
                        "id": "src",
                        "type": "test.devices.Source",
                        "position": {"x": 0, "y": 0},
                        "properties": {"rate": 2.5},
                    },
                    {
                        "id": "sink",
                        "type": "test.devices.Sink",
                        "position": {"x": 100, "y": 0},
                        "properties": {"threshold": 0.25},
                    },
                ],
                "connections": [
                    {
                        "source": {"device": "src", "port": "out"},
                        "target": {"device": "sink", "port": "in"},
                    }
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return path
