from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from qureed.diagram import Diagram
from qureed.project import QureedProject


@dataclass(frozen=True)
class RuntimeDevice:
    id: str
    source: str
    category: str
    name: str
    class_path: str


@dataclass(frozen=True)
class RuntimeDeviceDetails:
    id: str
    source: str
    class_path: str
    display_name: str
    category: str
    properties: tuple[dict, ...]
    ports: tuple[dict, ...]
    doc: str
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class RuntimeSpec:
    class_path: str
    source: str
    category: str
    path: Path
    valid: bool = True


@dataclass(frozen=True)
class RuntimeSpecGeneration:
    output_dir: Path
    written: tuple[Path, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class RuntimeValidation:
    valid: bool
    errors: tuple[str, ...]


@dataclass(frozen=True)
class RuntimeScript:
    path: Path | None
    content: str


@dataclass(frozen=True)
class RuntimeDiagram:
    path: Path
    diagram: Diagram


@dataclass(frozen=True)
class RuntimeProject:
    project: QureedProject
