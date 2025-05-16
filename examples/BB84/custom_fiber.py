import math
from enum import Enum
from typing import Any, Dict
from qureed.devices import GenericDevice
from qureed.devices.port import Port
from qureed.devices.wrappers import des_proc
from qureed.signals import QuantumOpticalPulseSignal, QOPSignalType
from qureed.assets import icon_list


class CustomFiber(GenericDevice):
    """
    Custom Optical Fiber Device (Example)

    This example device simulates the behavior of an optical fiber in the
    BB84 or other photonic quantum communication setups. It introduces a
    propagation delay based on the fiber length and refractive index, and
    applies a wavelength dependent phase shift to the quantum state in Fock
    basis.

    The fiber's delay and phase shift are derived from classical fiber optics:
    - Delay: computed as `length / (c / n)` where `c` is the speed of light in
      vacuum and `n` is the refractive index.
    - Phase shift: calculated as `π · n · length / wavelength`, applied as a
      `PhaseShift` operation to the Fock state.

    Ports:
    ------
    - input: float
        Fiber length in meters (default: 100 m).
    - n: float
        Refractive index of the fiber material (default: 1.45).

    GUI Metadata:
    -------------
    - gui_name: str
        Returns "Custom Fiber"
    - gui_icon: str
        Uses the fiber icon from the asset list.

    Backend Compatibility:
    ----------------------
    - photon_weave: Implements delay and phase shift on the Fock space

    Notes:
    ------
    - The signal must include `central_wavelength` in its metadata to compute
      the correct phase shift. Otherwise, a `ValueError` is raised.
    - Only `END`-type signals are phase-shifted; `START` signals are delayed
      but untouched.

    Example:
    --------
    >>> fiber = CustomFiber()
    >>> fiber.set_property("length", 150)
    >>> fiber.set_property("n", 1.468)
    """

    @property
    def gui_name(self) -> str:
        return "Custom Fiber"

    @property
    def gui_icon(self) -> str:
        return icon_list.FIBER

    properties: Dict[str, Dict[str, Any]] = {
        "length": {"type": float, "value": 100},  # meters
        "n": {"type": float, "value": 1.45},
    }

    # <<< type hints >>>
    class Ports(Enum):
        input = "input"
        output = "output"

    port_definitions = {
        "input": Port(
            direction="input", signal_type=QuantumOpticalPulseSignal
        ),
        "output": Port(
            direction="output", signal_type=QuantumOpticalPulseSignal
        ),
    }

    @des_proc(backend="photon_weave")
    def proc_pw(self):
        """
        PhotonWeave backend simulation process.

        Waits for incoming `QuantumOpticalPulseSignal`s on the `input` port.
        When an `END` signal is received:
        - Applies a wavelength-dependent phase shift to the Fock state.
        - All signals (`START` and `END`) are delayed based on fiber length
          and refractive index.
        - Emits the signal on the `output` port after the simulated delay.

        Raises:
        -------
        ValueError
            If the signal lacks the required `central_wavelength` metadata.
        """
        from photon_weave.constants import C0
        from photon_weave.operation import Operation, FockOperationType

        n = self.get_property("n")
        length = self.get_property("length")
        v = C0 / n  # Actual speed of the light in the medium
        delay = length / v

        while True:
            signal = yield self.receive(self.Ports.input)
            if signal.type is QOPSignalType.END:
                wavelength = signal.metadata.get("central_wavelength", None)
                if wavelength is None:
                    raise ValueError(
                        "central_wavelenght metadata is missing " "in signal"
                    )
                phase_shift = math.pi * n * length / wavelength
                op = Operation(FockOperationType.PhaseShift, phi=phase_shift)
                signal.payload.fock.apply_operation(op)
            yield self.sim_env.timeout(delay)
            self.send(self.Ports.output, signal)
