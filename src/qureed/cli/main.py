from __future__ import annotations

import argparse
import inspect
import os
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from qureed.cli.devices import (
    devices_inspect_command,
    devices_list_command,
)
from qureed.cli.diagrams import (
    diagrams_create_command,
    diagrams_validate_command,
)
from qureed.cli.project import project_init_command
from qureed.cli.scripts import scripts_generate_command
from qureed.cli.specs import specs_generate_command, specs_validate_command
from qureed.cli.specs import specs_list_command
from qureed.diagram import DiagramError
from qureed.project import ProjectConfigError
from qureed.registry import DeviceDiscoveryError, camel_to_snake
from qureed.scriptgen import ScriptGenerationError


def get_template_env():
    package_root = Path(__file__).resolve().parent.parent
    templates_path = package_root / "templates"
    return Environment(loader=FileSystemLoader(templates_path))


def list_signals():
    import qureed.signals

    signals = []
    for name, obj in inspect.getmembers(sys.modules["qureed.signals"]):
        if inspect.isclass(obj):
            signals.append(name)
    return signals


def list_icons():
    from qureed.assets import icon_list

    icons = [None]
    for name, obj in inspect.getmembers(icon_list):
        if isinstance(obj, str) and name.isupper():
            icons.append(name)
    return icons


def get_user_choice(options):
    for index, option in enumerate(options, start=1):
        print(f"{index}. {option}")
    choice = int(input("Select an option: "))
    while choice < 1 or choice > len(options):
        print("Invalid selection, please try again.")
        choice = int(input("Select an option: "))
    return options[choice - 1]


def template_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create device templates for qureed"
    )
    parser.add_argument(
        "--path", help="Path to the device template", required=True
    )
    parser.add_argument("--name", help="New ClassName", required=True)
    args = parser.parse_args(argv)
    normalized_path = args.path.rstrip("/")

    print(f"You have provided the path: {normalized_path}")
    if input("Is this path correct? (y/n): ").strip().lower() != "y":
        print("Operation cancelled.")
        return 1

    in_port_num = int(input("How many input ports does the device have?  "))
    out_port_num = int(input("How many output ports does the device have?  "))
    input_ports = {}
    output_ports = {}
    signal_types = list_signals()
    for i in range(in_port_num):
        label = input(f"Label of input port with index {i}: ")
        s_type = get_user_choice(signal_types)
        input_ports[label] = s_type

    for i in range(out_port_num):
        label = input(f"Label of output port with index {i}: ")
        s_type = get_user_choice(signal_types)
        output_ports[label] = s_type

    icon = get_user_choice(list_icons())

    template = get_template_env().get_template("device_template.jinja")
    output = template.render(
        name=args.name,
        input_ports=input_ports,
        output_ports=output_ports,
        gui_icon=icon,
    )
    print(output)
    if input("Save?(y/n): ").strip().lower() != "y":
        print("Operation cancelled.")
        return 1

    name = camel_to_snake(args.name)
    with open(f"{normalized_path}/{name}.py", "w", encoding="utf-8") as file:
        file.write(output)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="qureed")
    subparsers = parser.add_subparsers(dest="command", required=True)

    project = subparsers.add_parser("project", help="Manage QuReed projects")
    project_subparsers = project.add_subparsers(
        dest="project_command", required=True
    )
    project_init = project_subparsers.add_parser(
        "init", help="Create a qureed.toml project file"
    )
    project_init.add_argument(
        "path", nargs="?", default=".", help="Project directory"
    )
    project_init.add_argument("--name", help="Project name")
    project_init.add_argument(
        "--no-specs",
        action="store_true",
        help="Skip initial device spec generation",
    )
    project_init.set_defaults(func=project_init_command)

    devices = subparsers.add_parser("devices", help="Inspect device registry")
    devices_subparsers = devices.add_subparsers(
        dest="devices_command", required=True
    )
    devices_list = devices_subparsers.add_parser(
        "list", help="List available devices"
    )
    devices_list.set_defaults(func=devices_list_command)
    devices_inspect = devices_subparsers.add_parser(
        "inspect", help="Inspect a device"
    )
    devices_inspect.add_argument("identifier", help="Device id or class path")
    devices_inspect.set_defaults(func=devices_inspect_command)

    specs = subparsers.add_parser(
        "specs", help="Generate and validate static specs"
    )
    specs_subparsers = specs.add_subparsers(
        dest="specs_command", required=True
    )
    specs_generate = specs_subparsers.add_parser(
        "generate", help="Generate static device specs"
    )
    specs_generate.set_defaults(func=specs_generate_command)
    specs_validate = specs_subparsers.add_parser(
        "validate", help="Validate generated device specs"
    )
    specs_validate.set_defaults(func=specs_validate_command)
    specs_list = specs_subparsers.add_parser(
        "list", help="List generated device specs"
    )
    specs_list.set_defaults(func=specs_list_command)

    diagrams = subparsers.add_parser(
        "diagrams", help="Create and validate diagram JSON"
    )
    diagrams_subparsers = diagrams.add_subparsers(
        dest="diagrams_command", required=True
    )
    diagrams_create = diagrams_subparsers.add_parser(
        "create", help="Create an empty diagram"
    )
    diagrams_create.add_argument("path", help="Diagram path")
    diagrams_create.set_defaults(func=diagrams_create_command)
    diagrams_validate = diagrams_subparsers.add_parser(
        "validate", help="Validate a diagram"
    )
    diagrams_validate.add_argument("path", help="Diagram path")
    diagrams_validate.set_defaults(func=diagrams_validate_command)

    scripts = subparsers.add_parser(
        "scripts", help="Generate Python scripts from diagrams"
    )
    scripts_subparsers = scripts.add_subparsers(
        dest="scripts_command", required=True
    )
    scripts_generate = scripts_subparsers.add_parser(
        "generate", help="Generate a Python script from a diagram"
    )
    scripts_generate.add_argument("diagram_path", help="Diagram path")
    scripts_generate.add_argument("--output", help="Output script path")
    scripts_generate.set_defaults(func=scripts_generate_command)

    template = subparsers.add_parser(
        "template", help="Create a device template interactively"
    )
    template.add_argument("--path", required=True)
    template.add_argument("--name", required=True)
    template.set_defaults(
        func=lambda args: template_main(
            ["--path", args.path, "--name", args.name]
        )
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    if os.path.basename(sys.argv[0]) == "qureed-template":
        return template_main(argv)

    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (
        DeviceDiscoveryError,
        FileExistsError,
        KeyError,
        ProjectConfigError,
        DiagramError,
        ScriptGenerationError,
    ) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
