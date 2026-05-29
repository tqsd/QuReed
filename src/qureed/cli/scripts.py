from __future__ import annotations

import argparse

from qureed.interface.runtime import load_project


def scripts_generate_command(args: argparse.Namespace) -> int:
    service = load_project()
    result = service.generate_script(args.diagram_path, args.output)
    print(f"Generated {result.path}")
    return 0
