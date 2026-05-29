from __future__ import annotations

import json
from pathlib import Path

from qureed.cli.main import main
from qureed.interface.project import ProjectNotFoundError, load_project


def test_project_init_creates_qureed_toml(tmp_path: Path, capsys) -> None:
    project_dir = tmp_path / "example"

    exit_code = main(["project", "init", str(project_dir), "--name", "demo"])

    assert exit_code == 0
    project_file = project_dir / "qureed.toml"
    assert project_file.exists()
    assert (project_dir / "devices").is_dir()
    assert (project_dir / "specs" / "devices").is_dir()
    assert (project_dir / "diagrams").is_dir()
    assert (project_dir / "scripts").is_dir()
    assert list((project_dir / "specs" / "devices").glob("*.json"))
    project_text = project_file.read_text(encoding="utf-8")
    assert 'name = "demo"' in project_text
    assert "[paths]" in project_text
    assert 'custom_devices = ["devices"]' in project_text
    assert 'specs = "specs/devices"' in project_text
    assert 'diagrams = "diagrams"' in project_text
    assert 'scripts = "scripts"' in project_text
    assert "Created" in capsys.readouterr().out


def test_project_init_no_specs_skips_generation(
    tmp_path: Path, capsys
) -> None:
    project_dir = tmp_path / "example"

    exit_code = main(
        ["project", "init", str(project_dir), "--name", "demo", "--no-specs"]
    )

    assert exit_code == 0
    assert (project_dir / "devices").is_dir()
    assert (project_dir / "specs" / "devices").is_dir()
    assert (project_dir / "diagrams").is_dir()
    assert (project_dir / "scripts").is_dir()
    assert not list((project_dir / "specs" / "devices").glob("*.json"))
    assert "Generated" not in capsys.readouterr().out


def test_project_loader_discovers_from_nested_directory(
    tmp_path: Path, monkeypatch
) -> None:
    project_dir = tmp_path / "example"
    assert main(["project", "init", str(project_dir), "--no-specs"]) == 0
    nested = project_dir / "diagrams" / "nested"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)

    project = load_project()

    assert project.root == project_dir.resolve()
    assert project.path == (project_dir / "qureed.toml").resolve()
    assert project.name == "example"


def test_project_loader_resolves_paths_relative_to_root(
    tmp_path: Path,
) -> None:
    project_dir = tmp_path / "example"
    assert main(["project", "init", str(project_dir), "--no-specs"]) == 0

    project = load_project(project_dir / "scripts")

    assert project.custom_device_paths == (
        (project_dir / "devices").resolve(),
    )
    assert project.spec_output_path == (
        project_dir / "specs" / "devices"
    ).resolve()
    assert project.diagrams_path == (project_dir / "diagrams").resolve()
    assert project.scripts_path == (project_dir / "scripts").resolve()


def test_project_loader_missing_project_error(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)

    try:
        load_project()
    except ProjectNotFoundError as exc:
        assert "No qureed.toml found" in str(exc)
    else:
        raise AssertionError("Expected ProjectNotFoundError")


def test_devices_list_includes_builtin_source(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    project_dir = tmp_path / "example"
    assert main(["project", "init", str(project_dir), "--no-specs"]) == 0
    monkeypatch.chdir(project_dir)

    exit_code = main(["devices", "list"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "lossy_fiber" in output
    assert "builtin" in output
    assert "qureed.devices.fibers.lossy_fiber.LossyFiber" in output


def test_devices_list_includes_project_source(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    (tmp_path / "custom_devices.py").write_text(
        "\n".join(
            [
                "class CustomDevice:",
                "    properties = {'gain': {'type': float, 'value': 1.0}}",
                "    port_definitions = {}",
                "    @property",
                "    def gui_name(self):",
                "        return 'Custom Device'",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "qureed.toml").write_text(
        "\n".join(
            [
                "[project]",
                'name = "demo"',
                "",
                "[devices]",
                'class_paths = ["custom_devices.CustomDevice"]',
                'paths = ["devices"]',
                "",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["devices", "list"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "custom_device" in output
    assert "project" in output
    assert "custom_devices.CustomDevice" in output


def test_devices_list_works_from_nested_project_directory(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    project_dir = tmp_path / "example"
    assert main(["project", "init", str(project_dir), "--no-specs"]) == 0
    nested = project_dir / "scripts"
    monkeypatch.chdir(nested)

    exit_code = main(["devices", "list"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "lossy_fiber" in output
    assert "builtin" in output


def test_devices_inspect_accepts_class_path(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    project_dir = tmp_path / "example"
    assert main(["project", "init", str(project_dir), "--no-specs"]) == 0
    monkeypatch.chdir(project_dir)

    exit_code = main(
        [
            "devices",
            "inspect",
            "qureed.devices.fibers.lossy_fiber.LossyFiber",
        ]
    )

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "id: lossy_fiber" in output
    assert "source: builtin" in output


def test_specs_generate_writes_stable_device_specs(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    (tmp_path / "spec_custom_devices.py").write_text(
        "\n".join(
            [
                "class CustomDevice:",
                "    properties = {'gain': {'type': float, 'value': 1.0}}",
                "    port_definitions = {}",
                "    @property",
                "    def gui_name(self):",
                "        return 'Custom Device'",
                "    @property",
                "    def gui_icon(self):",
                "        return 'custom.svg'",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "qureed.toml").write_text(
        "\n".join(
            [
                "[project]",
                'name = "demo"',
                "",
                "[devices]",
                'class_paths = ["spec_custom_devices.CustomDevice"]',
                'paths = ["devices"]',
                "",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["specs", "generate"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Generated" in output
    specs = load_specs(tmp_path / "specs" / "devices")
    custom_spec = specs["spec_custom_devices.CustomDevice"]
    assert custom_spec["id"] == "spec_custom_devices.CustomDevice"
    assert custom_spec["source"] == "project"
    assert custom_spec["gui_name"] == "Custom Device"
    assert custom_spec["icon"] == "custom.svg"
    assert custom_spec["properties"] == {
        "gain": {"type": "float", "default": 1.0}
    }
    assert "qureed.devices.fibers.lossy_fiber.LossyFiber" in specs


def test_specs_validate_accepts_generated_specs(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    exit_code = main(["project", "init", str(tmp_path), "--no-specs"])
    assert exit_code == 0
    monkeypatch.chdir(tmp_path)

    assert main(["specs", "generate"]) == 0
    assert main(["specs", "validate"]) == 0

    assert "Validated" in capsys.readouterr().out


def test_specs_list_works_from_nested_project_directory(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    project_dir = tmp_path / "example"
    assert main(["project", "init", str(project_dir)]) == 0
    nested = project_dir / "scripts"
    monkeypatch.chdir(nested)

    exit_code = main(["specs", "list"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "class_path" in output
    assert "qureed.devices.fibers.lossy_fiber.LossyFiber" in output


def test_gui_command_starts_packaged_gui(monkeypatch) -> None:
    calls = []

    def fake_run_gui(**kwargs):
        calls.append(kwargs)

    monkeypatch.setattr("qureed.gui.main.run_gui", fake_run_gui)

    exit_code = main(
        [
            "gui",
            "--host",
            "127.0.0.2",
            "--port",
            "8123",
            "--project-root",
            ".",
            "--open",
        ]
    )

    assert exit_code == 0
    assert calls == [
        {
            "host": "127.0.0.2",
            "port": 8123,
            "project_root": ".",
            "open_browser": True,
        }
    ]


def load_specs(spec_dir: Path) -> dict[str, dict]:
    specs = {}
    for path in spec_dir.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        specs[data["class_path"]] = data
    return specs
