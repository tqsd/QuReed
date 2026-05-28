from __future__ import annotations

import argparse
import inspect
import os
import sys
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from qureed.device_registry import (
    BuiltinDeviceProvider,
    DeviceDiscoveryError,
    DeviceRegistry,
    ProjectDeviceProvider,
    camel_to_snake,
    describe_device,
)
from qureed.project import create_project, load_project
from qureed.specs import generate_device_specs, validate_device_specs


def get_template_env():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    templates_path = os.path.join(dir_path, "templates")
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


def build_registry(project=None) -> DeviceRegistry:
    project = project if project is not None else load_project()
    return DeviceRegistry(
        [BuiltinDeviceProvider(), ProjectDeviceProvider(project)]
    )


def project_init_command(args: argparse.Namespace) -> int:
    path = create_project(Path(args.path), name=args.name)
    print(f"Created {path}")
    if not args.no_specs:
        project = load_project(path.parent)
        if project is None:
            raise DeviceDiscoveryError(f"Could not load project at {path}")
        result = generate_device_specs(build_registry(project), project)
        print(
            f"Generated {len(result.written)} device specs "
            f"in {result.output_dir}"
        )
        for warning in result.warnings:
            print(f"warning: {warning}", file=sys.stderr)
    return 0


def devices_list_command(args: argparse.Namespace) -> int:
    registry = build_registry()
    rows = [
        (
            record.id,
            record.source,
            record.category,
            record.display_name,
            record.class_path,
        )
        for record in registry.all()
    ]
    print_table(("id", "source", "category", "name", "class_path"), rows)
    return 0


def devices_inspect_command(args: argparse.Namespace) -> int:
    registry = build_registry()
    record = registry.find(args.identifier)
    data = describe_device(record)
    print_device(data)
    return 0


def specs_generate_command(args: argparse.Namespace) -> int:
    project = require_project()
    result = generate_device_specs(build_registry(project), project)
    print(
        f"Generated {len(result.written)} device specs "
        f"in {result.output_dir}"
    )
    for warning in result.warnings:
        print(f"warning: {warning}", file=sys.stderr)
    return 0


def specs_validate_command(args: argparse.Namespace) -> int:
    project = require_project()
    result = validate_device_specs(project)
    if result.valid:
        print(f"Validated {len(result.checked)} device specs")
        return 0

    for error in result.errors:
        print(f"error: {error}", file=sys.stderr)
    return 1


def require_project():
    project = load_project()
    if project is None:
        raise DeviceDiscoveryError(
            "No qureed.toml found; run 'qureed project init' first"
        )
    return project


def print_table(headers: tuple[str, ...], rows: list[tuple[Any, ...]]) -> None:
    widths = [
        max(len(str(row[index])) for row in [headers, *rows])
        for index in range(len(headers))
    ]
    print(
        "  ".join(header.ljust(widths[i]) for i, header in enumerate(headers))
    )
    print("  ".join("-" * width for width in widths))
    for row in rows:
        print(
            "  ".join(
                str(value).ljust(widths[i]) for i, value in enumerate(row)
            )
        )


def print_device(data: dict[str, Any]) -> None:
    print(f"id: {data['id']}")
    print(f"source: {data['source']}")
    print(f"class_path: {data['class_path']}")
    print(f"display_name: {data['display_name']}")
    print(f"category: {data['category']}")
    print("properties:")
    for prop in data["properties"]:
        print(
            f"  - {prop['name']}: type={prop['type']} "
            f"default={prop['default']!r}"
        )
    print("ports:")
    for port in data["ports"]:
        print(
            f"  - {port['name']}: direction={port['direction']} "
            f"signal_type={port['signal_type']}"
        )
    if data["doc"]:
        summary = data["doc"].splitlines()[0]
        print(f"summary: {summary}")


def main(argv: list[str] | None = None) -> int:
    if os.path.basename(sys.argv[0]) == "qureed-template":
        return template_main(argv)

    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (DeviceDiscoveryError, FileExistsError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
