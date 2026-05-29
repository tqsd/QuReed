from __future__ import annotations

import argparse
import sys
from pathlib import Path

from qureed.interface.project import QureedProject, load_project
from qureed.interface.runtime import load_project as load_runtime_project


def diagrams_create_command(args: argparse.Namespace) -> int:
    result = load_runtime_project().create_diagram(args.path)
    print(f"Created {result.path}")
    return 0


def diagrams_validate_command(args: argparse.Namespace) -> int:
    service = load_runtime_project()
    path = service.resolve_diagram_path(args.path)
    result = service.validate_diagram(path)
    if result.valid:
        print(f"Validated {path}")
        return 0

    for error in result.errors:
        print(f"error: {error}", file=sys.stderr)
    return 1


def resolve_diagram_path(project: QureedProject, path: str) -> Path:
    candidate = Path(path).expanduser()
    if candidate.is_absolute():
        return candidate
    return (project.diagrams_path / candidate).resolve()
