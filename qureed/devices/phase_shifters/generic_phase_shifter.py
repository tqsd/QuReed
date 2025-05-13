from abc import ABC
from enum import Enum
from typing import Dict, Any

from qureed.assets import icon_list
from qureed.signals import (
    QuantumOpticalPulseSignal,
    FloatSignal,
)

from qureed.devices.wrappers import des_proc
from qureed.devices.port import Port
from qureed.devices.generic_device import GenericDevice


class GenericPhaseShifter(GenericDevice, ABC):
    """
    Abstract base class for all optical phase shifter devices in
    the QuReed simulation framework.

    `GenericPhaseShifter` provides a standard interface and port
    configuration for components that apply a phase shift to incoming
    quantum optical signals.
    The phase value can be configured via a dynamic input port or
    through a static property.

    Key Features:
    -------------
    - Defines three ports by defalud:
      - `'input'` (`QuantumOpticalPulseSignal`): receives the quantum
        optical signal.
      - `'output'` (`QuantumOpticalPulseSignal`): emits the phase-shifted
        signal
      - `'phi'` (`QuantumOpticalPulseSignal`): optionally receives a
        `FloatSignal` to update the phase during simulation.
    - Provides a `phi_proc` coroutine to dynamically update the phase during
      simulation.
    - Subclasses must implement the actual quantum operation using
      `@des_proc(backend=...)`

    Subclass Responsibilities:
    --------------------------
    - Implement simulation logic using one or more `@des_proc` methods.
    - Optionally override `gui_icon` to change the graphical icon in the UI.

    Ports:
    ------
    - input (input)   : Accepts a `QuantumOpticalPulseSignal`
    - output (output) : Emits a `QuantumOpticalPulseSignal` with phase shift
      applied
    - phi (input)     : Accepts a `FloatSignal` to dynamically update the
      phase angle

    Properties:
    -----------
    - phi : float
        The phase shift (in radians) applied to the incoming quantum signal

    GUI Medatada:
    -------------
    gui_icon: str
        Returns a symbolic constant representing the icon for phase shifter
        devices. Subclasses can reimplement `gui_icon`.

    Example:
    --------
    >>> class IdealPhaseShifter(GenericPhaseShifter):
    ...     @des_proc(backend="photon_weave")
    ...     def proc_pw(self):
    ...         from phoron_weave.operation import Operation, FockOperationType
    ...         while True:
    ...             signal = yield self.receive(self.Ports.input)
    ...             if signal.type is QOPSignalType.START:
    ...                 self.send(self.ports.output, signal)
    ...             elif signal.type is QOPSignalType.END:
    ...                 phi = self.get_property("phi")
    ...                 ps_op = Operation(
    ...                     FockOperationType.PhaseShift,
    ...                     phi=phi
    ...                 )
    ...                 signal.payload.fock.apply_operation(ps_op)
    ...                 self.send(self.Ports.output, signal)
    """

    properties: Dict[str, Dict[str, Any]] = {
        "phi": {"type": float},
    }

    # <<< static hint for LSP autocomplete >>>
    class Ports(Enum):
        input = "input"
        output = "output"
        phi = "phi"

    # <<< end of type hint >>>

    port_definitions = {
        "input": Port(
            direction="input", signal_type=QuantumOpticalPulseSignal
        ),
        "output": Port(
            direction="output", signal_type=QuantumOpticalPulseSignal
        ),
        "phi": Port(direction="input", signal_type=FloatSignal),
    }

    @property
    def gui_icon(self) -> str:
        return icon_list.PHASE_SHIFT

    @des_proc
    def phi_proc(self):
        """
        Simulation  process that dynamically updates the phase shift property.

        This coroutine listens for incoming `FloatSignal`s on the `phi` port.
        Each signal is expected to carry a floating-point value representing
        the new phase angle (in radians). Upon receiving such a signal, the
        method updates the internal `phi` property accordingly.

        This allows external components (e.g., classical control circuits) to
        dynamically control the phase shift applied by the device during
        simulation.

        Signal Flow:
        ------------
        - Input: `phi` (`FloatSignal` with new phase value)

        Behaviour:
        ----------
        - Waits for a `FloatSignal` on the `phi` port
        - Extracts the phase angle (`float`) from the signal
        - Sets the `phi` property on the device to the new value
        """
        while True:
            phi_signal = yield self.receive(self.Ports.phi)
            self.set_property("phi", float(phi_signal.value))
