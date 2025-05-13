from typing import Dict, Any, cast

from .generic_detector import GenericDetectorDevice
from qureed.signals import IntSignal, QuantumOpticalPulseSignal, QOPSignalType
from qureed.devices import des_proc


class IdealDetector(GenericDetectorDevice):
    """
    Ideal Detector Device

    The `IdealDetector` is a simulation device within the QuReed simulation
    framework that performs projective quantum measurements on incoming
    quantum optical pulses. It operates using `photon_weave` backend and
    emits classical detection results.

    Upon receiving `END`-type `QuantumOpticalPulseSignal`, the detector:
    - Extracts the underlying `Envelope` object
    - Performs a measurement in the Fock and polarization bases
    - Emits an `IntSignal` containing the Fock outcome, with the polarization
      stored in metadata.

    Ports:
    ------
    - input (input)   : Accepts `QuantumOpticalPulseSignal`s from upstream
      sources
    - output (output) : Emits `IntSignal` with measurement results

    Properties:
    -----------
    - delay : float
        A fixed time delay (in seconds) to wait before emitting the measurement
        results

    Backend Compatibility:
    ----------------------
    This device defines a `@des_proc(backend="photon_weave")` method
    (`proc_pw`) which handles quantum signal measurement using
    PhotonWeave's `Envelope` abstraction.

    Example:
    --------
    >>> detector = IdealDetector()
    >>> detector.set_property("delay", 1e-9)
    """

    properties: Dict[str, Dict[str, Any]] = {
        "delay": {"type": float, "value": 1e-9}
    }

    @property
    def gui_name(self) -> str:
        return "Ideal Detector"

    @des_proc(backend="photon_weave")
    def proc_pw(self):
        """
        Simulation process for the PhotonWeave backend.

        This coroutine listens for `QuantumOpticalPulseSignal`s on the `input`
        port. Upon receiving a signal of type `END`, it extracts the embedded
        `Envelope`, performs a projective quantum measurement, and emits
        `IntSignal` with the result.

        The emitted signal contains:
        - `value`: the result of the Fock measurement
        - `metadata`: the polarization measurement outcome

        A fixed delay (from `delay` property) is applied before the result is
        emitted, simulating detectors's latency.

        Signal Flow:
        ------------
        - Input: `input` (`QuantumOpticalPulseSignal` of type `END`)
        - Output: `output` (`IntSignal` with measurement result)

        Behavior:
        ---------
        - Waits for `END` signal
        - Extracts ENvelope and performs quantum measurement
        - Emits `IntSignal` with result after `delay` time
        """
        from photon_weave.state.envelope import Envelope

        delay = self.get_property("delay")

        while True:
            signal: QuantumOpticalPulseSignal = yield self.receive(
                self.Ports.input
            )
            if signal.type is QOPSignalType.END:
                envelope = cast(Envelope, signal.payload)
                outcome = envelope.measure()
                fock_measurement = outcome[envelope.fock]
                polarization_measurement = outcome[envelope.polarization]
                out_signal = IntSignal(
                    value=fock_measurement,
                    metadata={"polarization": polarization_measurement},
                )
                yield self.sim_env.timeout(delay)
                self.send(self.Ports.output, out_signal)
