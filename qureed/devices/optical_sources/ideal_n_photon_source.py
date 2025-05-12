from enum import Enum
from typing import Dict, Any
from mpmath import mpf

from qureed.signals.trigger_signal import TriggerSignal

from .generic_optical_source import GenericOpticalSourceDevice
from qureed.devices.wrappers import des_proc
from qureed.signals import QuantumOpticalPulseSignal
from qureed.devices import Port
from qureed.signals.value_signals import IntSignal


class IdealNPhotonSource(GenericOpticalSourceDevice):

    properties: Dict[str, Dict[str, Any]] = {
        "photonNum": {"type": int, "value": 1},
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
        while True:
            int_signal = yield self.receive(self.Ports.photon_num)
            self.set_property("photonNum", int(int_signal.value))

    @des_proc(backend="photon_weave")
    def proc_pw(self):
        from photon_weave.state.envelope import Envelope

        while True:
            _ = yield self.receive(self.Ports.trigger)

            photon_num = self.get_property("photonNum")
            env = Envelope()
            env.fock.state = photon_num

            start_signal, end_signal = QuantumOpticalPulseSignal.create_pair(
                payload=env
            )

            self.send(self.Ports.output, start_signal)
            yield self.sim_env.timeout(mpf("1e-9"))
            self.send(self.Ports.output, end_signal)
