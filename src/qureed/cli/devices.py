from __future__ import annotations

import argparse
from typing import Any

from qureed.runtime import load_project


def devices_list_command(args: argparse.Namespace) -> int:
    service = load_project()
    rows = [
        (
            device.id,
            device.source,
            device.category,
            device.name,
            device.class_path,
        )
        for device in service.list_available_devices()
    ]
    print_table(("id", "source", "category", "name", "class_path"), rows)
    return 0


def devices_inspect_command(args: argparse.Namespace) -> int:
    device = load_project().inspect_device(args.identifier)
    print_device(
        {
            "id": device.id,
            "source": device.source,
            "class_path": device.class_path,
            "display_name": device.display_name,
            "category": device.category,
            "properties": device.properties,
            "ports": device.ports,
            "doc": device.doc,
        }
    )
    return 0


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
