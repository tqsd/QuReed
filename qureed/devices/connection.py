from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .exceptions import PortDirectionException

if TYPE_CHECKING:
    from qureed.devices.generic_device import GenericDevice
    from qureed.signals import GenericSignal

@dataclass(frozen=True)
class Connection:
    source_device: GenericDevice
    source_port: str
    sink_device: GenericDevice
    sink_port: str
    signal_type: type[GenericSignal]

    def get_next_device_and_port(self):
        return self.sink_device, self.sink_port

def resolve_connection_direction(
    local_device: GenericDevice,
    local_port: Union[str, Enum],
    local_dir: Literal["input", "output"],
    remote_device: GenericDevice,
    remote_port: Union[str, Enum],
    remote_dir: Literal["input", "output"],
    ):
    if local_dir == "output" and remote_dir == "input":
        return local_device, local_port, remote_device, remote_port
    if local_dir == "input" and remote_dir == "output":
        return remote_device, remote_port, local_device, local_port
    raise PortDirectionException(f"Cannot connect {local_dir} to {remote_dir}")
