from __future__ import annotations

import argparse
import sys

from qureed.cli.devices import print_table
from qureed.interface.runtime import load_project


def specs_generate_command(args: argparse.Namespace) -> int:
    result = load_project().generate_specs()
    print(
        f"Generated {len(result.written)} device specs "
        f"in {result.output_dir}"
    )
    for warning in result.warnings:
        print(f"warning: {warning}", file=sys.stderr)
    return 0


def specs_validate_command(args: argparse.Namespace) -> int:
    result = load_project().validate_specs()
    if result.valid:
        print("Validated device specs")
        return 0

    for error in result.errors:
        print(f"error: {error}", file=sys.stderr)
    return 1


def specs_list_command(args: argparse.Namespace) -> int:
    rows = [
        (spec.class_path, spec.source, spec.category, spec.path)
        for spec in load_project().list_available_specs()
    ]
    print_table(("class_path", "source", "category", "path"), rows)
    return 0
