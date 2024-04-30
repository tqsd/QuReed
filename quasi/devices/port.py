"""
Device port definitions
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Type, Literal, Optional
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from quasi.devices.generic_device import GenericDevice
    from quasi.signals.generic_signal import GenericSignal


@dataclass
class Port:
    """
    Port Dataclass
    """

    label: str
    direction: Literal["input", "output"]
    signal: Optional["GenericSignal"]
    signal_type: Type["GenericSignal"]
    device: "GenericDevice"

    def __post_init__(self):
        if None in [self.label, self.direction, self.signal_type]:
            raise PortMissingAttributesException(
                "label, direction and signal_type must be specified"
            )

    def disconnect(self):
        if self.signal is None:
            return
        signal = self.signal
        self.signal = None
        ports = signal.ports
        other_ports = [p for p in ports if p is not self]
        for p in other_ports:
            if isinstance(p.signal, list):
                p.signal.remove(signal)
            else:
                p.signal = None
                


class PortMissingAttributesException(Exception):
    """
    Raised when Attributes are not specified
    """
