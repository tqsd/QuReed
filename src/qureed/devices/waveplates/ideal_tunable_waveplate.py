from enum import Enum
from typing import Dict, Any
import math

from qureed.simulation import Simulation
from qureed.signals.quantum_optical_pulse_signal import (
    QuantumOpticalPulseSignal,
    QOPSignalType,
)
from qureed.signals.value_signals import FloatSignal
from qureed.devices.port import Port
from qureed.devices.wrappers import des_proc
from .generic_waveplate import GenericWaveplateDevice


class IdealTunableWaveplate(GenericWaveplateDevice):
    r"""
    Ideal Tunable Waveplate Device

    This device models an ideal tunable waveplate. It processes incoming
    `QuantumOpticalPulseSignal`s on port `input` and `FloatSignal`s on port
    `control`. The `FloatSignal`s on `control` port dictate the operation
    applied to the `QuantumOpticalPulseSignal`s on port `input`.

    .. math::

        \hat{R}_Y(\theta) =
        \begin{bmatrix}
            \cos\left(\frac{\theta}{2}\right) &
            -\sin\left(\frac{\theta}{2}\right) \\
            \sin\left(\frac{\theta}{2}\right) &
            \cos\left(\frac{\theta}{2}\right)
        \end{bmatrix}

    Ports:
    ------
    - input (input): Receive `QuantumOpticalPulseSignal`
    - control (input): Receive `FloatSignal`

    Properties:
    -----------
    - angle: float
        The angle dictating the `RY` operation on the polarization space
        of the incoming `QuantumOpticalPulseSignal`.

    Backend Compatibility:
    ----------------------
    - photon_weave: suported via `_polarization_operation_photon_weave`

    Example:
    --------
    >>> itw = IdealTunableWaveplate()
    >>> idw.set_property("angle", 3.14)
    """

    def __init__(self, uid=None, **kwargs):
        super().__init__(uid, **kwargs)
        self.delay = 1e-11

    properties: Dict[str, Dict[str, Any]] = {
        "angle": {"type": float, "value": math.pi}
    }

    @property
    def gui_name(self) -> str:
        return "Ideal Tunable Waveplate"

    # <<< static hint for LSP autocomplete >>>
    class Ports(Enum):  # type: ignore
        input = "input"
        output = "output"
        control = "control"

    port_definitions = {
        **GenericWaveplateDevice.port_definitions,
        "control": Port(direction="input", signal_type=FloatSignal),
    }

    @des_proc
    def control_proc(self):
        """
        Simulation Process that listens for the updates to the control
        angle.

        This coroutine continuously listens for `FloatSignal` on the
        `control` port. Upon receiving a signal, it updates the `angle`
        property of the device to reflect the new control angle.

        Signal Flow:
        ------------
        - Input: `control` (`FloatSignal`)

        Behavior:
        ---------
        - Waits for a new `FloatSignal`
        - Extracts the value from the signal
        - Sets the `angle` property accordingly

        Raises:
        -------
        `TypeError`: If the received signal does not have a valid `float`
        value.

        """
        while True:
            float_signal = yield self.receive(self.Ports.control)
            self.set_property("angle", float(float_signal.value))

    def _send_with_delay(self, signal: QuantumOpticalPulseSignal):
        """
        Sends the signals out of the `output` port with some delay.

        Arguments:
        ----------
        signal: `QuantumOpticalPulseSignal`
            The signal to be sent out
        """

        def __send():
            yield self.sim_env.timeout(self.delay)
            self.send(self.Ports.output, signal)

        self.sim_env.process(__send())

    @des_proc
    def proc_pw(self):
        """
        Main simulation process for `IdealTunableWaveplate`.

        This coroutine runs in the SimPy event loop. It processes `START` and
        `END` signals from port `input`. `START` signals are sent on with
        delay. `END` signals trigger the actual changing of the polarization.

        A fixed delay is applied before emitting signals, simulating, the time
        light needs to travel through IdealTunableWaveplate.

        Signal Flow:
        ------------
        - Input: `input` (`QuantumOpticalPulseSignal`)
        - Output: `output` (`QuantumOpticalPulseSignal`)

        Behavior:
        ---------
        - Waits for either `START` or `END` input signals
        - If `START` signal is received it is emitted with delay.
        - If `END` signal is received operation is applied.
        """
        while True:
            signal = yield self.receive(self.Ports.input)
            if signal.type is QOPSignalType.START:
                self._send_with_delay(signal)
                continue
            self._polarization_operation(signal)
            self._send_with_delay(signal)

    def _polarization_operation(self, signal: QuantumOpticalPulseSignal):
        """
        Dispatches the polarization operation to a backend-specific method.

        The operation applies a `RY` operation where the angle is set by
        the device's `angle` property.

        Arguments:
        ----------
        signal: `QuantumOpticalPulseSignal`
             Signal to be operated on.
        """
        method_name = f"_polarization_operation_{Simulation().backend}"
        method = getattr(self, method_name, None)
        if method is None:
            raise NotImplementedError(
                "_polarization_operation not implemented for backend "
                f"{Simulation().backend}; expected method {method_name}"
            )
        return method(signal)

    def _polarization_operation_photon_weave(
        self, signal: QuantumOpticalPulseSignal
    ):
        """
        Photon Weave implementation of the `RY` operation on the polarization
        space.

        Arguments:
        ----------
        signal: `QuantumOpticalPulseSignal`
            signal containing the `Envelope` to apply the operation to
        """
        from photon_weave.operation import Operation, PolarizationOperationType

        op = Operation(
            PolarizationOperationType.RY, theta=self.get_property("angle")
        )
        signal.payload.polarization.apply_operation(op)
