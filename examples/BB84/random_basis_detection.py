from typing import Dict, Any
from enum import Enum
import math
import random

from qureed.devices.port import Port
from qureed.devices.wrappers import des_proc
from qureed.signals.quantum_optical_pulse_signal import (
    QOPSignalType,
    QuantumOpticalPulseSignal,
)
from qureed.signals.trigger_signal import TriggerSignal
from qureed.signals.value_signals import FloatSignal
from tests.devices.test_generic_device import GenericDevice


class RandomBasisDetection(GenericDevice):

    properties: Dict[str, Dict[str, Any]] = {}

    @property
    def gui_name(self) -> str:
        return "Random Basis Detection"

    @property
    def gui_icon(self) -> str:
        return "None"

    # <<< static hint for LSP autocomplete >>>
    class Ports(Enum):
        clk = "clk"
        rnd = "rnd"
        input = "input"

    # <<< end of type hint >>>

    port_definitions = {
        "clk": Port(direction="input", signal_type=TriggerSignal),
        "rnd": Port(direction="output", signal_type=FloatSignal),
        "input": Port(
            direction="input", signal_type=QuantumOpticalPulseSignal
        ),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._measured_bits = []
        self._current_basis = 0

    @des_proc
    def proc(self):
        send_delay = 1e-10
        while True:
            yield self.receive(self.Ports.clk)
            self._current_basis = random.randint(0, 1)
            angle = 0 if self._current_basis == 0 else -math.pi / 2
            yield self.sim_env.timeout(send_delay)
            self.send(self.Ports.rnd, FloatSignal(value=angle))

    @des_proc(backend="photon_weave")
    def proc_pw(self):
        while True:
            signal = yield self.receive(self.Ports.input)
            if signal.type is QOPSignalType.START:
                continue
            envelope = signal.payload
            outcome = envelope.measure()
            self._measured_bits.append(
                (self._current_basis, outcome[envelope.polarization])
            )
