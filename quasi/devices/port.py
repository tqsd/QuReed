"""
Device port definitions
"""
from typing import Type, Literal, Dict
from dataclasses import dataclass

@dataclass
class Port:
    """
    Port Dataclass
    """
    label: str
    direction: Literal["input", "output"]
    signal: GenericSignal
    signal_type: Type[GenericSignal]
    device: Type[GenericDevice]

    def __post_init__(self):
        if None in [self.label, self.direction, self.signal_type]:
            raise PortMissingAttributesException(
                "label, direction and signal_type must be specified")

