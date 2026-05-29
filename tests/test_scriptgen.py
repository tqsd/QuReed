from __future__ import annotations

import json
from pathlib import Path

from qureed.cli.main import main
from qureed.interface.project import load_project
from qureed.interface.scriptgen import generate_script_from_file


def test_script_generation_is_deterministic(tmp_path: Path) -> None:
    project_dir = create_project_with_specs(tmp_path)
    diagram_path = write_valid_diagram(project_dir)
    project = load_project(project_dir)

    first = generate_script_from_file(diagram_path, project).script
    second = generate_script_from_file(diagram_path, project).script

    assert first == second


def test_script_generation_imports_from_specs(tmp_path: Path) -> None:
    project_dir = create_project_with_specs(tmp_path)
    diagram_path = write_valid_diagram(project_dir)
    project = load_project(project_dir)

    script = generate_script_from_file(diagram_path, project).script

    assert "from test.devices import Sink, Source" not in script
    assert "from test.devices import Sink" in script
    assert "from test.devices import Source" in script


def test_script_generation_assigns_properties(tmp_path: Path) -> None:
    project_dir = create_project_with_specs(tmp_path)
    diagram_path = write_valid_diagram(project_dir)
    project = load_project(project_dir)

    script = generate_script_from_file(diagram_path, project).script

    assert "src.set_property('rate', 2.5)" in script
    assert "sink.set_property('threshold', 0.25)" in script


def test_invalid_diagram_fails_before_generation(
    tmp_path: Path, monkeypatch
) -> None:
    project_dir = create_project_with_specs(tmp_path)
    diagram_path = project_dir / "diagrams" / "invalid.json"
    write_diagram(
        diagram_path,
        devices=[
            {
                "id": "missing",
                "type": "test.devices.Missing",
                "position": {"x": 0, "y": 0},
                "properties": {},
            }
        ],
        connections=[],
    )
    monkeypatch.chdir(project_dir)

    output_path = project_dir / "scripts" / "invalid.py"
    assert (
        main(
            [
                "scripts",
                "generate",
                "invalid.json",
                "--output",
                str(output_path),
            ]
        )
        == 1
    )
    assert not output_path.exists()


def test_script_generate_creates_output_file(
    tmp_path: Path, monkeypatch
) -> None:
    project_dir = create_project_with_specs(tmp_path)
    write_valid_diagram(project_dir)
    monkeypatch.chdir(project_dir)

    assert main(["scripts", "generate", "valid.json"]) == 0

    output_path = project_dir / "scripts" / "valid.py"
    assert output_path.exists()
    script = output_path.read_text(encoding="utf-8")
    assert "def build_experiment():" in script
    assert "src.connect(src.Ports['out'], sink, sink.Ports['in'],)" in script


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
    write_diagram(
        path,
        devices=[
            source_device(properties={"rate": 2.5}),
            sink_device(properties={"threshold": 0.25}),
        ],
        connections=[
            {
                "source": {"device": "src", "port": "out"},
                "target": {"device": "sink", "port": "in"},
            }
        ],
    )
    return path


def write_diagram(path: Path, *, devices: list[dict], connections: list[dict]):
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "devices": devices,
                "connections": connections,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def source_device(properties: dict | None = None) -> dict:
    return {
        "id": "src",
        "type": "test.devices.Source",
        "position": {"x": 0, "y": 0},
        "properties": properties or {},
    }


def sink_device(properties: dict | None = None) -> dict:
    return {
        "id": "sink",
        "type": "test.devices.Sink",
        "position": {"x": 100, "y": 0},
        "properties": properties or {},
    }
