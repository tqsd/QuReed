from __future__ import annotations
from typing import Dict, Any, Union
import random

from qureed.simulation import Simulation
from qureed.devices.wrappers import des_proc
from qureed.devices.exceptions import SimulationException

from .generic_detector import GenericDetectorDevice
from qureed.signals import IntSignal, QOPSignalType


class ImperfectDetector(GenericDetectorDevice):
    """
    Imperfect Detector Device

    This device simulates a more realistic photonic detector by including
    features such as timing jitter, constant detection delay, dark counts,
    and dead time. It is backend-dispatchable via the `measure()` method.

    Key Features:
    -------------
    - Fixed detector delay (`delay`)
    - Gaussian-distributed detector (`detectorJitter`)
    - Optional envelope jitter support (not implemented)
    - Dark count simulation via `darkCountRateHz`
    - Dead time suppression via `deadTime`

    Properties:
    -----------
    - delay (float)               : Constant measurement delay
    - detectorJitter (float)      : Standard deviation of the detection jitter
                                  : (in seconds)
    - enableEnvelopeJitter (bool) : If True, include envelope jitter
                                  : (not yet used)
    - darkCountRateHz (float)     : Rate (Hz) of dark counts to simulate.
    - deadTime (float)            : Duration after a detectionduring which the
                                  : detector is inactive.

    Ports:
    ------
    - input  (`QuantumOpticalPulseSignal`)
    - output (`IntSignal`)
    """

    properties: Dict[str, Dict[str, Any]] = {
        "delay": {"type": float, "value": 1e-9},
        "detectorJitter": {"type": float, "value": 30e-12},
        "enableEnvelopeJitter": {"type": bool, "value": True},
        "darkCountRateHz": {"type": float, "value": 0.0},
        "deadTime": {"type": float, "value": 0.0},
    }

    @property
    def gui_name(self) -> str:
        return "Imperfect Detector"

    def __init__(self, uid=None, **kwargs):
        super().__init__(uid, **kwargs)
        self._last_measurement: Union[Any, float] = -float("inf")

    def measure(
        self, envelope: Any = None, dark_count: bool = False
    ) -> IntSignal:
        """
        Dispatches measurement logic to the appropriate backend-specific
        method.

        Arguments:
        ----------
        envelope: Any
            The quantum state container to measure
        dark_count: bool
            If True, simulate a dark count event.

        Raises:
        -------
        NotImplementedError: If no `measure_*` method is implemented for
            current backend
        """
        method_name = f"_measure_{Simulation().backend}"
        method = getattr(self, method_name, None)
        if method is None:
            raise NotImplementedError(
                "Measurement method not implemented for backend "
                f"'{Simulation().backend}'"
            )
        return method(envelope, dark_count)

    def send_with_dark_time(self, signal: IntSignal):
        """
        Sends the signal to the `output`port if it's not suppressed by the
        detector's dead time.

        Arguments:
        ----------
        signal: IntSignal
            The signal to send

        Notes:
        ------
        - If the signal represents a photon (value>0), it resets dead time
          window.
        - If within dead time or the signal is vacuum, it's suppressed.
        """
        dead_time = self.get_property("deadTime")
        if (
            signal.value <= 0
            or self.sim_env.now < self._last_measurement + dead_time
        ):
            self.log("Detection during dead time")
            return
        self._last_measurement = self.sim_env.now
        self.send(self.Ports.output, signal)

    def _measure_photon_weave(
        self, envelope=None, dark_count: bool = False
    ) -> IntSignal:
        """
        PhotonWeave-specific measurement logic.

        If `dark_count` is true, simulates a random photon detection using
        a dummy envelope. Otherwise, performs a real measurement on the
        provided envelope.

        Arguments:
        ----------
        envelope: Optional[Envelope]
            The quantum state container
        dark_count: bool
            Wether this is a dark count.

        Returns:
        --------
        IntSignal:
            Measurement outcome with Fock value and polarization metadata.

        Raises:
        -------
        - SimulationException: if dark_count is True and envelope is also
            provided
        """
        from photon_weave.state.envelope import Envelope
        from photon_weave.state.polarization import PolarizationLabel

        if dark_count and envelope is not None:
            raise SimulationException(
                "Both 'dark_count' and 'envelope' cannot be provided "
                "at the same time"
            )

        if dark_count:
            envelope = Envelope()
            envelope.fock.state = 1
            envelope.polarization.state = PolarizationLabel.R

        if envelope is None:
            return IntSignal(value=0)

        outcome = envelope.measure()
        int_signal = IntSignal(
            value=outcome[envelope.fock],
            metadata={"polarization": outcome[envelope.polarization]},
        )
        return int_signal

    @des_proc
    def dark_count_proc(self):
        """
        Simulation process that simulates dark count generation over time.

        Behavior:
        ---------
        - Samples inter-arrival times from an exponential distribution
        - Waits for the time delay, performs a backend-dispatched dark count
          measurement.
        - Emits the signal via `send_with_dark_count`.

        Notes:
        ------
        - Behaviour is suppressed if `darkCountRateHZ <= 0`
        """
        dark_count_rate = self.get_property("darkCountRateHz")
        if dark_count_rate <= 0:
            yield self.sim_env.timeout(float("inf"))
        while dark_count_rate > 0:
            next_dark_count = random.expovariate(dark_count_rate)
            yield self.sim_env.timeout(next_dark_count)
            self.log("Scheduling dark count")
            out_signal = self.measure(dark_count=True)
            self.send_with_dark_time(out_signal)

    @des_proc(backend="photon_weave")
    def proc_pw(self):
        """
        Simulation process for the PhotonWeave backend.

        This coroutine listens for a incoming `QuantumOpticalPulseSignal`s on
        the `input` port. Upon receiving a signal of type `END`, it performs a
        realistic detection process by applying delay and jitter before
        measuring the quantum state and emitting a classical result.

        The detection includes:
        - A fixed delay (`delay` property)
        - A gaussian-distributed detector jitter (`detectorJitter` property)

        The `START`-type signals are ignored by this detector.

        Signal Flow:
        ------------
        - Input: `input` (`QuantumOpticalPulseSignal`)
        - Output: `output` (`IntSignal` with detection result)

        Behavior:
        ---------
        - Ignores `START`-type signals
        - Waits for `END`-type signals
        - Applies time delay and timing jitter
        - Performs backend-specific measurement(`measure()`)
        - Sends result using `send_with_dead_time()` with dead-time
          suppression
        """
        while True:
            in_signal = yield self.receive(self.Ports.input)
            if in_signal.type is QOPSignalType.START:
                continue
            envelope = in_signal.payload

            # Compute total delay
            base_delay = self.get_property("delay")
            jitter_std = self.get_property("detectorJitter")

            total_jitter = random.gauss(0, jitter_std)
            total_delay = max(0.0, base_delay + total_jitter)

            yield self.sim_env.timeout(total_delay)

            out_signal = self.measure(envelope)
            self.send_with_dark_time(out_signal)
