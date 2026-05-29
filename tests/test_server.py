from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
httpx = pytest.importorskip("httpx")

from qureed.cli.main import main
from qureed.server.app import create_app


def test_health_route(tmp_path: Path) -> None:
    response = request(create_project_with_specs(tmp_path), "GET", "/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_frontend_static_routes_are_served(tmp_path: Path) -> None:
    project_dir = create_project_with_specs(tmp_path)

    index_response = request(project_dir, "GET", "/")
    asset_response = request(
        project_dir, "GET", "/assets/qureed-gui.css"
    )

    assert index_response.status_code == 200
    assert "QuReed" in index_response.text
    assert asset_response.status_code == 200
    assert ".appShell" in asset_response.text


def test_project_route(tmp_path: Path) -> None:
    project_dir = create_project_with_specs(tmp_path)

    response = request(project_dir, "GET", "/project")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "project"
    assert data["root"] == str(project_dir.resolve())


def test_devices_and_specs_routes_read_specs(tmp_path: Path) -> None:
    project_dir = create_project_with_specs(tmp_path)

    devices_response = request(project_dir, "GET", "/devices")
    specs_response = request(project_dir, "GET", "/specs")

    assert devices_response.status_code == 200
    assert specs_response.status_code == 200
    device_types = {item["class_path"] for item in devices_response.json()}
    spec_types = {item["class_path"] for item in specs_response.json()}
    assert "test.devices.Source" in device_types
    assert "test.devices.Source" in spec_types
    source_spec = next(
        item
        for item in specs_response.json()
        if item["class_path"] == "test.devices.Source"
    )
    assert source_spec["gui_name"] == "test.devices.Source"
    assert source_spec["properties"] == {
        "rate": {"default": 1.0, "type": "float"}
    }


def test_diagram_validate_route(tmp_path: Path) -> None:
    project_dir = create_project_with_specs(tmp_path)
    write_valid_diagram(project_dir)

    response = request(
        project_dir,
        "POST",
        "/diagrams/validate",
        json={"path": "valid.json"},
    )

    assert response.status_code == 200
    assert response.json() == {"valid": True, "errors": []}


def test_diagram_save_and_load_routes(tmp_path: Path) -> None:
    project_dir = create_project_with_specs(tmp_path)
    diagram = {
        "version": 1,
        "devices": [
            {
                "id": "source_1",
                "type": "test.devices.Source",
                "position": {"x": 42, "y": 55},
                "properties": {"rate": 1.0},
            }
        ],
        "connections": [],
    }

    save_response = request(
        project_dir,
        "POST",
        "/diagrams/save",
        json={"path": "demo.json", "diagram": diagram},
    )
    load_response = request(
        project_dir,
        "GET",
        "/diagrams/load",
        params={"path": "demo.json"},
    )

    assert save_response.status_code == 200
    assert load_response.status_code == 200
    assert load_response.json()["diagram"] == diagram
    assert (project_dir / "diagrams" / "demo.json").exists()


def test_script_generate_route(tmp_path: Path) -> None:
    project_dir = create_project_with_specs(tmp_path)
    write_valid_diagram(project_dir)

    response = request(
        project_dir,
        "POST",
        "/scripts/generate",
        json={"diagram_path": "valid.json", "output": "valid.py"},
    )

    assert response.status_code == 200
    data = response.json()
    expected_path = (project_dir / "scripts" / "valid.py").resolve()
    assert data["path"] == str(expected_path)
    assert "from test.devices import Source" in data["content"]
    assert (project_dir / "scripts" / "valid.py").exists()


def request(
    project_dir: Path,
    method: str,
    path: str,
    **kwargs,
) -> httpx.Response:
    async def run_request() -> httpx.Response:
        transport = httpx.ASGITransport(app=create_app(project_dir))
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(run_request())


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
