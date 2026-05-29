from __future__ import annotations

import json
from pathlib import Path

from qureed.cli.main import main
from qureed.diagram import (
    Diagram,
    DiagramConnection,
    DiagramDevice,
    DiagramPosition,
    load_diagram,
    save_diagram,
)


def test_diagrams_create_empty_diagram(tmp_path: Path, monkeypatch) -> None:
    project_dir = create_project(tmp_path)
    monkeypatch.chdir(project_dir)

    assert main(["diagrams", "create", "empty.json"]) == 0

    data = json.loads(
        (project_dir / "diagrams" / "empty.json").read_text(
            encoding="utf-8"
        )
    )
    assert data == {"connections": [], "devices": [], "version": 1}


def test_load_save_diagram_json(tmp_path: Path) -> None:
    path = tmp_path / "diagram.json"
    diagram = Diagram(
        devices=(
            DiagramDevice(
                id="src",
                type="test.Source",
                position=DiagramPosition(x=10, y=20),
                properties={"rate": 2},
            ),
        ),
        connections=(
            DiagramConnection(
                id="c1",
                source_device="src",
                source_port="out",
                target_device="sink",
                target_port="in",
            ),
        ),
    )

    save_diagram(diagram, path)
    loaded = load_diagram(path)

    assert loaded == diagram


def test_validate_correct_diagram(tmp_path: Path, monkeypatch) -> None:
    project_dir = create_project_with_specs(tmp_path)
    write_valid_diagram(project_dir / "diagrams" / "valid.json")
    monkeypatch.chdir(project_dir)

    assert main(["diagrams", "validate", "valid.json"]) == 0


def test_validate_detects_unknown_device_ids(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    project_dir = create_project_with_specs(tmp_path)
    write_diagram(
        project_dir / "diagrams" / "bad.json",
        devices=[source_device()],
        connections=[
            connection(
                source_device="src",
                source_port="out",
                target_device="missing",
                target_port="in",
            )
        ],
    )
    monkeypatch.chdir(project_dir)

    assert main(["diagrams", "validate", "bad.json"]) == 1
    assert "unknown target device missing" in capsys.readouterr().err


def test_validate_detects_unknown_ports(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    project_dir = create_project_with_specs(tmp_path)
    write_diagram(
        project_dir / "diagrams" / "bad.json",
        devices=[source_device(), sink_device()],
        connections=[
            connection(
                source_device="src",
                source_port="missing",
                target_device="sink",
                target_port="in",
            )
        ],
    )
    monkeypatch.chdir(project_dir)

    assert main(["diagrams", "validate", "bad.json"]) == 1
    assert "unknown source port src.missing" in capsys.readouterr().err


def test_validate_detects_missing_required_properties(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    project_dir = create_project_with_specs(tmp_path)
    write_spec(
        project_dir / "specs" / "devices" / "required.json",
        class_path="test.Required",
        ports={},
        properties={"required": {"type": "float"}},
    )
    write_diagram(
        project_dir / "diagrams" / "bad.json",
        devices=[
            {
                "id": "required",
                "type": "test.Required",
                "position": {"x": 0, "y": 0},
                "properties": {},
            }
        ],
        connections=[],
    )
    monkeypatch.chdir(project_dir)

    assert main(["diagrams", "validate", "bad.json"]) == 1
    assert "missing property required" in capsys.readouterr().err


def test_validate_detects_invalid_connection_directions(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    project_dir = create_project_with_specs(tmp_path)
    write_diagram(
        project_dir / "diagrams" / "bad.json",
        devices=[source_device(), source_device("other")],
        connections=[
            connection(
                source_device="src",
                source_port="out",
                target_device="other",
                target_port="out",
            )
        ],
    )
    monkeypatch.chdir(project_dir)

    assert main(["diagrams", "validate", "bad.json"]) == 1
    assert "output to output" in capsys.readouterr().err


def test_validate_from_nested_project_directory(
    tmp_path: Path, monkeypatch
) -> None:
    project_dir = create_project_with_specs(tmp_path)
    write_valid_diagram(project_dir / "diagrams" / "valid.json")
    nested = project_dir / "scripts"
    monkeypatch.chdir(nested)

    assert main(["diagrams", "validate", "valid.json"]) == 0


def create_project(tmp_path: Path) -> Path:
    project_dir = tmp_path / "project"
    assert main(["project", "init", str(project_dir), "--no-specs"]) == 0
    return project_dir


def create_project_with_specs(tmp_path: Path) -> Path:
    project_dir = create_project(tmp_path)
    spec_dir = project_dir / "specs" / "devices"
    write_spec(
        spec_dir / "source.json",
        class_path="test.Source",
        ports={"out": {"direction": "output", "signal_type": "Pulse"}},
        properties={"rate": {"type": "float", "default": 1.0}},
    )
    write_spec(
        spec_dir / "sink.json",
        class_path="test.Sink",
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


def write_valid_diagram(path: Path) -> None:
    write_diagram(
        path,
        devices=[source_device(), sink_device()],
        connections=[
            connection(
                source_device="src",
                source_port="out",
                target_device="sink",
                target_port="in",
            )
        ],
    )


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


def source_device(device_id: str = "src") -> dict:
    return {
        "id": device_id,
        "type": "test.Source",
        "position": {"x": 0, "y": 0},
        "properties": {},
    }


def sink_device() -> dict:
    return {
        "id": "sink",
        "type": "test.Sink",
        "position": {"x": 100, "y": 0},
        "properties": {},
    }


def connection(
    *,
    source_device: str,
    source_port: str,
    target_device: str,
    target_port: str,
) -> dict:
    return {
        "source": {"device": source_device, "port": source_port},
        "target": {"device": target_device, "port": target_port},
    }
