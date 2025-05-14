from abc import ABC
from enum import Enum
from typing import Dict, Any
import math

from qureed.devices.generic_device import GenericDevice
from qureed.devices.port import Port
from qureed.signals import QuantumOpticalPulseSignal
from qureed.assets import icon_list


class GenericBeamSplitterDevice(GenericDevice, ABC):
    properties: Dict[str, Dict[str, Any]] = {
        "eta": {"type": float, "value": math.pi / 4}
    }

    # <<< static hint for LSP autocomplete >>>
    class Ports(Enum):
        A = "A"
        B = "B"
        C = "C"
        D = "D"

    # <<< end of type hint >>>

    port_definitions = {
        "A": Port(direction="input", signal_type=QuantumOpticalPulseSignal),
        "B": Port(direction="input", signal_type=QuantumOpticalPulseSignal),
        "C": Port(direction="output", signal_type=QuantumOpticalPulseSignal),
        "D": Port(direction="output", signal_type=QuantumOpticalPulseSignal),
    }

    @property
    def gui_icon(self) -> str:
        return icon_list.BEAM_SPLITTER
