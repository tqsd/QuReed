from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DiagramPosition:
    x: float = 0
    y: float = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DiagramPosition":
        return cls(x=data.get("x", 0), y=data.get("y", 0))

    def to_dict(self) -> dict[str, float]:
        return {"x": self.x, "y": self.y}


@dataclass(frozen=True)
class DiagramDevice:
    id: str
    type: str
    position: DiagramPosition = field(default_factory=DiagramPosition)
    properties: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DiagramDevice":
        return cls(
            id=data["id"],
            type=data["type"],
            position=DiagramPosition.from_dict(data.get("position", {})),
            properties=dict(data.get("properties", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "position": self.position.to_dict(),
            "properties": self.properties,
        }


@dataclass(frozen=True)
class DiagramConnection:
    source_device: str
    source_port: str
    target_device: str
    target_port: str
    id: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DiagramConnection":
        source = data["source"]
        target = data["target"]
        return cls(
            id=data.get("id"),
            source_device=source["device"],
            source_port=source["port"],
            target_device=target["device"],
            target_port=target["port"],
        )

    def to_dict(self) -> dict[str, Any]:
        data = {
            "source": {
                "device": self.source_device,
                "port": self.source_port,
            },
            "target": {
                "device": self.target_device,
                "port": self.target_port,
            },
        }
        if self.id is not None:
            data["id"] = self.id
        return data


@dataclass(frozen=True)
class Diagram:
    version: int = 1
    devices: tuple[DiagramDevice, ...] = ()
    connections: tuple[DiagramConnection, ...] = ()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Diagram":
        return cls(
            version=data.get("version", 1),
            devices=tuple(
                DiagramDevice.from_dict(item)
                for item in data.get("devices", [])
            ),
            connections=tuple(
                DiagramConnection.from_dict(item)
                for item in data.get("connections", [])
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "devices": [device.to_dict() for device in self.devices],
            "connections": [
                connection.to_dict() for connection in self.connections
            ],
        }
