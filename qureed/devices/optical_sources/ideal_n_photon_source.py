from enum import Enum
from typing import Dict, Any
from mpmath import mpf

from qureed.signals.trigger_signal import TriggerSignal

from .generic_optical_source import GenericOpticalSourceDevice
from qureed.devices.wrappers import des_proc
from qureed.signals import QuantumOpticalPulseSignal, IntSignal
from qureed.devices import Port


class IdealNPhotonSource(GenericOpticalSourceDevice):
    """
    Ideal N-Photon Source Device

    This class defines the `IdealNPhotonSource`, a configurable optical source
    device within the QuReed simulation framework. It emits a quantum optical
    pulse containing an exact number of photons |n>, modeled by appropriate
    backend and emitted within a `QuantumOpticalPulseSignal`.

    The source responds to a `TriggerSignal` on its `trigger` port, and emits a
    START/END pulse pair to the `output` port.

    The source is implemented using PhotonWeave backend and encapsulates the
    state emitted in PhotonWeave's `Envelope`, with the Fock state set to the
    desired photon number.

    Ports:
    ------
    - trigger (input)    : Accepts a `TriggerSignal` to initiate emission
    - photon_num (input) : Accepts `IntSignal` to dynamically set the number
        of photons.
    - output (output)    : Emits a `QuantumOpticalPulseSignal` pair containing
        the reference to the quantum state.

    Properties:
    -----------
    - photonNum: int
        The number of photons to emit. Can be set statically or dynamically via
        the `photon_num` port.
    - pulseDuration: float
        The duration of the pulse. Implicitly defines the temporal/spectral
        properties of the pulse.
    - centralWavelength : float
        Central Wavelength of the pulse (in meters). Used for envelope
        generation.

    Backend Compatibility:
    ----------------------
    This device defines a `@des_proc(backend="photon_weave")` method
    (`proc_pw`) that interfaces with the `photon` backend and generates a
    proper `Envelope` object containing the state.

    Example:
    --------
    >>> source = IdealNPhotonSource()
    >>> source.set_property("photonNum", 2)
    >>> source.set_property("centralWavelength", 1310e-9)
    >>> source.set_property("pulseDuration", 1e-9)
    """

    properties: Dict[str, Dict[str, Any]] = {
        "photonNum": {"type": int, "value": 1},
        "pulseDuration": {"type": float, "value": 1e-9},
        "centralWavelength": {"type": float, "value": 1550e-9},
    }

    # <<< static hint for LSP autocomplete >>>
    class Ports(Enum):  # type: ignore[reportGeneralTypeIssues]
        trigger = "trigger"
        photon_num = "photon_num"
        output = "output"

    # <<< end of type hint >>>

    port_definitions = {
        "trigger": Port(direction="input", signal_type=TriggerSignal),
        "photon_num": Port(direction="input", signal_type=IntSignal),
        "output": Port(
            direction="output", signal_type=QuantumOpticalPulseSignal
        ),
    }

    @property
    def gui_name(self) -> str:
        return "Ideal n-photon source"

    @des_proc
    def photon_num_proc(self):
        """
        Simulation process that listens for the updates to the photon number.

        This coroutine continuously listens for `IntSignal`s on the
        `photon_num` port. Upon receiving a signal, it updates the
        `photonNum` property of the device to reflect the new photon count.

        This allows the number of photons emitted by the source to be
        dynamically configured during the simulation.

        Signal Flow:
        ------------
        - Input : `photon_num` (IntSignal)

        Behavior:
        ---------
        - Waits for a new `IntSignal`
        - Extracts the value from the signal
        - Sets the `photonNum` property accordingly

        Raises:
        -------
        TypeError: If the received signal does not have a valid integer value.

        """
        while True:
            int_signal = yield self.receive(self.Ports.photon_num)
            self.set_property("photonNum", int(int_signal.value))

    @des_proc(backend="photon_weave")
    def proc_pw(self):
        """
        Simulation process for the PhotonWeave backend.

        This coroutine listens for a `TriggerSignal` on the port.
        Upon receiving a trigger, it creates a PhotonWeave `Envelope`
        object, with the configured photon number (Fock state), and
        emits a START/END `QuantumOpticalPulseSignal` pair on the
        `output` port.

        A time delay (`5*pulse_duration`) is inserted between the START and
        END signal emissions to represent the temporal extent of the pulse.

        Signal Flow:
        ------------
        - Input: `trigger` (TriggerSignal)
        - Output: `output` (QuantumOpticalPulseSignal [START],
        followed by [END])

        Behavior:
        ---------
        - Reads the `photonNum` property to determine the Fock state (|n⟩)
        - Encapsulates the state in an `Envelope` from the PhotonWeave backend.
        - Sends START signal, waits `5*pulse_duration`, then sends the END
          signal.
        """
        from photon_weave.state.envelope import Envelope

        while True:
            _ = yield self.receive(self.Ports.trigger)

            photon_num = self.get_property("photonNum")
            pulse_duration = self.get_property("pulseDuration")
            env = Envelope()
            env.fock.state = photon_num

            start_signal, end_signal = QuantumOpticalPulseSignal.create_pair(
                payload=env, metadata={"pulse_duration": pulse_duration}
            )

            self.send(self.Ports.output, start_signal)
            yield self.sim_env.timeout(mpf(5 * pulse_duration))
            self.send(self.Ports.output, end_signal)
