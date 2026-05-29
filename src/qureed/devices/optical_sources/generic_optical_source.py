from abc import ABC
from enum import Enum
from typing import Dict, Any

from qureed.devices.generic_device import GenericDevice
from qureed.devices.port import Port
from qureed.signals import TriggerSignal
from qureed.assets import icon_list


class GenericOpticalSourceDevice(GenericDevice, ABC):
    """
    Abstract base class for all optical source devices in the
    QuReed simulation framework.

    `GenericOpticalSourceDevice` provides a common foundation for
    devices that emit quantum optical states, typically in response
    to a received `TriggerSignal`.

    Key Features:
    -------------
    - Defines a default `'trigger'` input port, which receives a
      `TriggerSignal`.
    - Subclasses are expected to define the appropriate output port(s).
    - Subclasses must implement simulation logic via
      `@des_proc(backend=...)` methods.

    Subclass Responsibilities:
    --------------------------
    - Redefine the `Ports` enum with at least a `'trigger'` and one or
      more `'output'` ports.
    - Reimplement `port_definitions` accordingly
    - Implement the simulation logic using one or more `@des_proc`
      methods (backend specific)
    - Optionally override the `gui_icon` property to change the source's icon.

    Ports:
    ------
    trigger: output
        Accepts a `TriggerSignal` to initiate photon emission.

    GUI Metadata:
    -------------
    gui_icon: str
        Returns a symbolic constant representing the icon for source
        devices. Subclasses can reimplement `gui_icon`.

    Example:
    --------
    >>> class IdealSinglePhotonSource(GenericOpticalSourceDevice):
    ...     properties = {
    ...         "wavelength": {
    ...           "type": float,
    ...           "value": 1550e-9
    ...         }
    ...     }
    ...
    ...     class Ports(Enum):
    ...         trigger = "trigger"
    ...         output = "output"
    ...
    ...     port_definitions = {
    ...         "trigger": Port(direction="input", signal_type=TriggerSignal),
    ...         "output": Port(
    ...           direction="output", signal_type=QuantumOpticalPulseSignal)
    ...     }
    ...
    ...     @property
    ...     def gui_name(self) -> str:
    ...         return "Ideal Source"
    ...
    ...     @des_proc(backend="photon_weave")
    ...     def proc_pw(self):
    ...         from photon_weave.state.envelope import Envelope
    ...
    ...         while True:
    ...             _ = yield self.receive(self.Ports.trigger)
    ...             env = Envelope()
    ...             env.fock.state = 1
    ...             s_sig, e_sig = QuantumOpticalPulseSignal.create_pair(
    ...                 payload = env
    ...             )
    ...             self.send(self.Ports.output, s_sig)
    ...             yield self.sim_env.timeout(mpf("1e-9"))
    ...             self.send(self.Ports.output, e_sig)
    """

    properties: Dict[str, Dict[str, Any]] = {}

    # <<< static hint for LSP autocomplete >>>
    class Ports(Enum):
        trigger = "trigger"

    # <<< end of type hint >>>

    port_definitions = {
        "trigger": Port(direction="input", signal_type=TriggerSignal)
    }

    @property
    def gui_icon(self) -> str:
        return icon_list.N_PHOTON_SOURCE
