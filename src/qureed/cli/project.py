from __future__ import annotations

import argparse
import sys
from pathlib import Path

from qureed.project import create_project
from qureed.runtime import load_project


def project_init_command(args: argparse.Namespace) -> int:
    path = create_project(Path(args.path), name=args.name)
    print(f"Created {path}")
    if not args.no_specs:
        result = load_project(path.parent).generate_specs()
        print(
            f"Generated {len(result.written)} device specs "
            f"in {result.output_dir}"
        )
        for warning in result.warnings:
            print(f"warning: {warning}", file=sys.stderr)
    return 0
