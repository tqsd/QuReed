from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectConfig:
    name: str
    custom_device_paths: tuple[str, ...]
    device_class_paths: tuple[str, ...]
    spec_output_path: str
    diagrams_path: str
    scripts_path: str


@dataclass(frozen=True)
class QureedProject:
    root: Path
    config_path: Path
    config: ProjectConfig
    custom_device_paths: tuple[Path, ...]
    spec_output_path: Path
    diagrams_path: Path
    scripts_path: Path

    @property
    def path(self) -> Path:
        return self.config_path

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def device_paths(self) -> tuple[str, ...]:
        return self.config.custom_device_paths

    @property
    def device_class_paths(self) -> tuple[str, ...]:
        return self.config.device_class_paths
