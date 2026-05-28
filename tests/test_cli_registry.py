from __future__ import annotations

import json
from pathlib import Path

from qureed.cli import main


def test_project_init_creates_qureed_toml(tmp_path: Path, capsys) -> None:
    project_dir = tmp_path / "example"

    exit_code = main(["project", "init", str(project_dir), "--name", "demo"])

    assert exit_code == 0
    project_file = project_dir / "qureed.toml"
    assert project_file.exists()
    assert (project_dir / "devices").is_dir()
    assert (project_dir / "specs" / "devices").is_dir()
    assert list((project_dir / "specs" / "devices").glob("*.json"))
    assert 'name = "demo"' in project_file.read_text(encoding="utf-8")
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
    assert not list((project_dir / "specs" / "devices").glob("*.json"))
    assert "Generated" not in capsys.readouterr().out


def test_devices_list_includes_builtin_source(capsys) -> None:
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


def test_devices_inspect_accepts_class_path(capsys) -> None:
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


def load_specs(spec_dir: Path) -> dict[str, dict]:
    specs = {}
    for path in spec_dir.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        specs[data["class_path"]] = data
    return specs
