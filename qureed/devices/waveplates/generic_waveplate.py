from abc import ABC
from enum import Enum
from typing import Dict, Any

from qureed.devices.generic_device import GenericDevice
from qureed.devices.port import Port
from qureed.assets import icon_list
from qureed.signals.quantum_optical_pulse_signal import (
    QuantumOpticalPulseSignal,
)


class GenericWaveplateDevice(GenericDevice, ABC):
    """
    Abstract base class for all waveplate devices in the Qureed simulation
    framework.

    `GenericWaveplateDevice` provides common foundation for devices that
    affect the polarization of the light.

    Key Features:
    -------------
    - Defines input and output `Ports` and `port_definitions`
    - Defines the `gui_icon` for the subclases

    Subclass Responsibilities:
    --------------------------
    - Optionally redefine `Ports` enum with desired ports.
    - Optionally reimplement `port_definitions` accordingly.
    - Implement simulation logic using one or more `@des_proc`
      methods (backend specific).
    - Optionally override the `gui_icon` property to change the
      waveplate's icon.

    Ports:
    ------
    input: input
        Accepts a `QuantumOpticalPulseSignal`
    output: output
        Emits `QuantumOpticalPulseSignal` with changed polarization

    GUI Metadata:
    -------------
    gui_icon:
        Returns a symbolic constant representing the icon for waveplate
        devices. Subclasses can reimplement `gui_icon`.
    """

    properties: Dict[str, Dict[str, Any]] = {}

    # <<< static hint for LSP autocomplete >>>
    class Ports(Enum):
        input = "input"
        output = "output"

    # <<< end of type hint >>>

    port_definitions = {
        "input": Port(
            direction="input", signal_type=QuantumOpticalPulseSignal
        ),
        "output": Port(
            direction="output", signal_type=QuantumOpticalPulseSignal
        ),
    }

    @property
    def gui_icon(self) -> str:
        return icon_list.WAVEPLATE
