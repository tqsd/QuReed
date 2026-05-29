from enum import Enum
import random
from typing import Dict, Any, Union
from mpmath import mpf

from qureed.signals import QuantumOpticalPulseSignal, TriggerSignal
from qureed.devices.wrappers import des_proc
from qureed.devices.port import Port

from .generic_optical_source import GenericOpticalSourceDevice


class QDEntangledPhotonSource(GenericOpticalSourceDevice):
    """
    Quantum Dot Entangled Photon Source

    This class implements a polarization-entangled photon pair source based
    based on a quantum dot biexciton-exciton cascade. The source emits two
    photons with polarization entanglement and realistic timing delays based
    on sampled biexciton and exciton lifetimes.

    Upon receiving a `TriggerSignal`, the device:
    - Samples emission delays for biexciton and exciton delays.
    - Creates four Fock states (depending on the backend) representing H/V
      polarization accross two temporal modes.
    - Applies an entangling operator to the Fock states.
    - Optionally applies a polraization shift corresponding to the
      fine-structure splitting (FSS)
    - Emits `QuantumOpticalPulseSignal`s representing the emittes pulses

    Ports:
    ------
    - trigger (input)  : Accepts a `TriggerSignal` to initiate emission.
    - output1 (output) : Emits photon signals (biexciton + optionally exciton)
    - output2 (output) : Emits exciton signals when filtering is enabled

    Proterties:
    -----------
    - centralWavelengthBiexciton : float
        Wavelength (in meters) for the biexciton photon.
    - centralWavelengthExciton : float
        Wavelength (in meters) for the exciton photon.
    - pulseDurationBiexciton : float
        Duration of the biexciton pulse.
    - pulseDurationExciton : float
        Duration of the exciton pulse.
    - biexcitonLifetime : float
        Lifetime (in s) used to sample biexciton emission delay.
    - excitonLifetime : float
        Lifetime (in s) used to sample exciton emission delay.
    - FFS : float
        Fine-structure splitting in μeV, used to compute a polarization phase.
    - filtering : bool
        If True, separates exciton output to `output2`, otherwise reuses
        `output1`.

    Backend Compatibility:
    ----------------------
    This device defines a `@des_proc(backend="photon_weave)` method (`proc_pw`)
    which:
    - Constructs the entangled state using symbolic expression and composite
      envelope.
    - Applies a polarization phase shift if FFS is non-zero.
    - Emits pulses via the SimPy simulation backend using realistic emission
      delays.

    Example:
    --------
    >>> dev = QDEntangledPhotonSource()
    >>> dev.set_property("FFS", 2.5)
    >>> dev.set_property("filtering", True)
    >>> dev.set_property("pulseDurationBiexciton", 1e-9)
    >>> dev.set_property("pulseDurationExciton", 1e-9)
    """

    properties: Dict[str, Dict[str, Any]] = {
        "centralWavelengthBiexciton": {"type": float, "value": 825e-9},
        "centralWavelengthExciton": {"type": float, "value": 825e-9},
        "pulseDurationBiexciton": {"type": float, "value": 1e-9},
        "pulseDurationExciton": {"type": float, "value": 1e-9},
        "biexcitonLifetime": {"type": float, "value": 1e-12},
        "excitonLifetime": {"type": float, "value": 1e-12},
        "FFS": {"type": float, "value": 0},
        "filtering": {"type": bool, "value": True},
    }

    # <<< static hint for LSP autocomplete >>>
    class Ports(Enum):  # type: ignore[reportGeneralTypeIssues]
        trigger = "trigger"
        output1 = "output1"
        output2 = "output2"

    # <<< end of type hint >>>

    port_definitions = {
        "trigger": Port(direction="input", signal_type=TriggerSignal),
        "output1": Port(
            direction="output", signal_type=QuantumOpticalPulseSignal
        ),
        "output2": Port(
            direction="output", signal_type=QuantumOpticalPulseSignal
        ),
    }

    @property
    def gui_name(self) -> str:
        return "QD Entangled Photon Source"

    def _sample_emission(self, property_name: str) -> Any:
        """
        Samples an emission delay based on an exponential distribution.

        This helper method retrieves the lifetime associated with the given
        property name and returns a sampled delay using an exponential
        distribution:

        .. math::

            f(t) = \\lambda e^{-\\lambda t}\\
            \\lambda = 1 / \\text{lifetime}

        If the lifetime is zero, the delay is set to 0 ps.

        Arguments:
        ----------
        proterty_name : str
            The name of the lifetime property to use (e.g., "excitonLifetime")

        Returns
        -------
        mpf
            A delay value (in seconds) sampled from an exponential distribution
            with the given lifetimes

        """
        lifetime = self.get_property(property_name)
        if lifetime == 0:
            return mpf(0)
        return mpf(random.expovariate(1.0 / lifetime))

    @property
    def next_exciton_emission(self) -> Any:
        return self._sample_emission("excitonLifetime")

    @property
    def next_biexciton_emission(self) -> Any:
        return self._sample_emission("biexcitonLifetime")

    def emit_pulse(
        self,
        port: Any,
        delay: Union[Any, float],
        start_signal: QuantumOpticalPulseSignal,
        end_signal: QuantumOpticalPulseSignal,
    ):
        """
        Emits a quantum optical pulse as a pair of START and END signals.

        This coroutine first waits for the specified delay before emitting the
        `start_signal`. It then waits for a duration extracted from the
        metadata field `"pulse_duration"` (defaulting to 1 ns), scaled by 5,
        and emits the `end_signal`.

        The temporal structure models a physical pulse shape by bounding it
        between a START and END event.

        Arguments:
        ----------
        port : Enum
            The output port (e.g., `self.Ports.output1`) to send the signals
            to.
        delay : float or mpf
            Delay before emitting the start signal (typically emission delay).
        start_signal : QuantumOpticalPulseSignal
            The signal representing the start of the pulse.
        end_signal : QuantumOpticalPulseSignal
            The signal representing the end of the pulse.
        """
        yield self.sim_env.timeout(delay)
        self.send(port, start_signal)

        duration = start_signal.metadata.get("pulse_duration")
        if duration is None:
            # TODO: Warning if the pulse duration is not set
            duration = 1e-9
        duration = 5 * duration

        yield self.sim_env.timeout(duration)
        self.send(port, end_signal)

    @des_proc(backend="photon_weave")
    def proc_pw(self):
        """
        PhotonWeave emission process for QD entangled photon generation.

        This coroutine is triggered upon receiving a `Triggesignal` and
        simulates the emission of an entangled photon pair via the
        biexciton-exciton cascade in a quantum dot.

        The process includes:
        - Sampling emission delays based on exponential lifetimes.
        - Creating four `Envelope` corresponging to H/V polarizations across
          two temporal modes.
        - Applying an entangling Fock-space operator to the composite state.
        - Applying a phase shift to vertical polarizations based on the
          configured FFS.
        - Creating pulse signals and dispatching them using `emit_pulse`
          coroutines.

        Emission timing is handled via SimPy subprocesses, allowing overlapping
        signals and correct modeling of asynchronous emission.

        Signal Flow:
        ------------
        - Input: `trigger` (`TriggerSignal`)
        - Output: `output1`, `output2` (`QuantumOpticalPulseSignal` pairs for
          each photon)

        Behavior:
        ---------
        - Applies symbolic operator using PhotonWeave backend
        - Dynamically applies polarization phase shift
        - Dispatches photon signals to the appropriate ports at appropriate
          times.
        """
        from photon_weave.state.envelope import Envelope
        from photon_weave.state.polarization import PolarizationLabel
        from photon_weave.state.fock import Fock
        from photon_weave.state.composite_envelope import CompositeEnvelope
        from photon_weave.operation import (
            Operation,
            CompositeOperationType,
            PolarizationOperationType,
        )
        from qureed.backends.photon_weave import (
            generate_entangling_operator,
            generate_polarization_phase_operator,
        )

        exciton_lambda = self.get_property("centralWavelengthExciton")
        biexciton_lambda = self.get_property("centralWavelengthBiexciton")

        while True:
            _ = yield self.receive(self.Ports.trigger)

            # Get emission delays
            biexciton_emission_delay = self.next_biexciton_emission
            exciton_emission_delay = self.next_exciton_emission

            env0H = Envelope(wavelength=biexciton_lambda)
            env0H.polarization.state = PolarizationLabel.H
            env0V = Envelope(wavelength=biexciton_lambda)
            env0V.polarization.state = PolarizationLabel.V
            env1H = Envelope(wavelength=exciton_lambda)
            env1H.polarization.state = PolarizationLabel.H
            env1V = Envelope(wavelength=exciton_lambda)

            env1V.polarization.state = PolarizationLabel.V

            # Define Entangling operation
            en_expr, en_context = generate_entangling_operator()
            op = Operation(
                CompositeOperationType.Expression,
                expr=en_expr,
                state_types=(Fock, Fock, Fock, Fock),
                context=en_context,
            )

            # Create product space
            ce = CompositeEnvelope(env0H, env0V, env1H, env1V)

            # Entangle the states
            ce.apply_operation(
                op, env0H.fock, env0V.fock, env1H.fock, env1V.fock
            )

            # Compute Phase operation
            hbar = 0.6582  # [uV*ps]
            phase = self.get_property("FFS") * exciton_emission_delay / hbar

            polarization_phase_operator = Operation(
                PolarizationOperationType.Custom,
                operator=generate_polarization_phase_operator(phase),
            )

            env0V.polarization.apply_operation(polarization_phase_operator)
            env1V.polarization.apply_operation(polarization_phase_operator)

            # Generate the signals
            sig_0H_start, sig_0H_end = QuantumOpticalPulseSignal.create_pair(
                payload=env0H,
                metadata={
                    "pulse_duration": self.get_property(
                        "pulseDurationBiexciton"
                    )
                },
            )

            sig_0V_start, sig_0V_end = QuantumOpticalPulseSignal.create_pair(
                payload=env0V,
                metadata={
                    "pulse_duration": self.get_property(
                        "pulseDurationBiexciton"
                    )
                },
            )

            sig_1H_start, sig_1H_end = QuantumOpticalPulseSignal.create_pair(
                payload=env1H,
                metadata={
                    "pulse_duration": self.get_property("pulseDurationExciton")
                },
            )

            sig_1V_start, sig_1V_end = QuantumOpticalPulseSignal.create_pair(
                payload=env1V,
                metadata={
                    "pulse_duration": self.get_property("pulseDurationExciton")
                },
            )

            # Schedule the DES emission as a separate coroutines
            self.sim_env.process(
                self.emit_pulse(
                    self.Ports.output1,
                    biexciton_emission_delay,
                    sig_0V_start,
                    sig_0V_end,
                )
            )
            self.sim_env.process(
                self.emit_pulse(
                    self.Ports.output1,
                    biexciton_emission_delay,
                    sig_0H_start,
                    sig_0H_end,
                )
            )

            yield self.sim_env.timeout(biexciton_emission_delay)
            port2 = (
                self.Ports.output2
                if self.get_property("filtering")
                else self.Ports.output1
            )

            self.sim_env.process(
                self.emit_pulse(
                    port2,
                    exciton_emission_delay,
                    sig_1V_start,
                    sig_1V_end,
                )
            )
            self.sim_env.process(
                self.emit_pulse(
                    port2,
                    exciton_emission_delay,
                    sig_1H_start,
                    sig_1H_end,
                )
            )
