from abc import ABC
from enum import Enum
from typing import Dict, Any

from qureed.assets import icon_list
from qureed.devices.generic_device import GenericDevice
from qureed.devices.port import Port
from qureed.signals.quantum_optical_pulse_signal import (
    QuantumOpticalPulseSignal,
)


class GenericFiber(GenericDevice, ABC):
    """
    Abstract base class for all fiber devices in the QuReed simulation
    framework.

    `GenericFiber` prodives a common foundation for devices that simulate
    an optical fiber.

    Key Features:
    -------------
    - Defines a default `'input'` input port, which receives a
      `QuantumOpticalPulseSignal`.
    - Defines a default `'output'` output port, which emits a
      `QuantumOpticalPulseSignal`.

    Subclass Responsibilities:
    - Optionally redefine `Ports` enum with desired ports.
    - Optionally reimplement `port_definitions` accordingly.
    - Implement the simulation logic using one or more `@des_proc`
      methods (backend specific).
    - Optionally override the `gui_icon` property to change the
      fiber's icon.
    - Implement `gui_name` property.

    Ports:
    ------
    input: input
        Accepts a `QuantumOpticalPulseSignal` signal
    output: output
        Emits a `QuantumOpticalPulseSignal` signal

    GUI Metadata:
    -------------
    gui_icon:
        Returns a symbolic constant representing the icon for fiber
        devices. Subclasses can reimplement `gui_icon`
    """

    properties: Dict[str, Dict[str, Any]] = {"length": {"type": float}}

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
        return icon_list.FIBER
