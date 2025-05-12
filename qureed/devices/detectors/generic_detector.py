from abc import ABC
from enum import Enum
from typing import Dict, Any

from qureed.devices.generic_device import GenericDevice
from qureed.devices.port import Port
from qureed.signals import IntSignal, QuantumOpticalPulseSignal
from qureed.assets import icon_list


class GenericDetectorDevice(GenericDevice, ABC):
    """
    Abstract base class for all detector devices in the
    QuReed simulation framework.

    `GenericDetectorDevice` provides a common foundation for
    devices that detect quantum optical states.

    Key Features:
    -------------
    - Defines a default `'input'` input port, which receives a
      `QuantumOpticalPulseSignal`.
    - Subclasses must implement simulatino logic via
      `@dec_proc(backend=...)` methods.

    Subclass Responsibilities:
    --------------------------
    - Optionally Redefine `Ports` enum with desired ports.
    - Optionally reimlement `port_definitions` accordingly.
    - Implement the simulation logic using one or more `@des_proc`
      methods (backend specific).
    - Optionally override the `gui_icon` property to change the
      detector's icon.

    Ports:
    ------
    input: input
        Accepts a `QuantumOpticalPulseSignal` to initiate detection.

    GUI Metadata:
    -------------
    gui_icon:
        Returns a symbolic constant representing the icon for detector
        devices. Subclasses can reimlement `gui_icon`.
    """

    properties: Dict[str, Dict[str, Any]] = {}

    # <<< static hint for LSP autocomplete >>>
    class Prots(Enum):
        input = "input"
        output = "output"

    # <<< end of type hint >>>

    port_definitions = {
        "input": Port(
            direction="input", signal_type=QuantumOpticalPulseSignal
        ),
        "output": Port(direction="output", signal_type=IntSignal),
    }

    @property
    def gui_icon(self) -> str:
        return icon_list.N_PHOTON_SOURCE
