from typing import Dict, Any
import math
import random
from enum import Enum
from qureed.devices import GenericDevice
from qureed.devices.port import Port
from qureed.devices.wrappers import des_proc
from qureed.signals.trigger_signal import TriggerSignal
from qureed.signals.value_signals import FloatSignal


class RandomBasisTrigger(GenericDevice):

    properties: Dict[str, Dict[str, Any]] = {"frequency": {"type": float}}

    @property
    def gui_name(self) -> str:
        return "Random Basis Trigger"

    @property
    def gui_icon(self) -> str:
        return "None"

    # <<< static hint for LSP autocomplete >>>
    class Ports(Enum):
        clk = "clk"
        random = "random"
        trigger = "trigger"

    # <<< end of type hint >>>

    port_definitions = {
        "clk": Port(direction="input", signal_type=TriggerSignal),
        "random": Port(direction="output", signal_type=FloatSignal),
        "trigger": Port(direction="output", signal_type=TriggerSignal),
    }

    def __init__(self, uid=None, **kwargs):
        super().__init__(uid, **kwargs)
        self._sent_bits = []

    @des_proc
    def proc(self):
        send_delay = 1 / (10 * self.get_property("frequency"))
        while True:
            yield self.receive(self.Ports.clk)
            yield self.sim_env.timeout(send_delay)

            basis = random.randint(0, 1)
            bit = random.randint(0, 1)
            self._sent_bits.append((basis, bit))

            if basis == 0:
                angle = 0 if bit == 0 else math.pi
            else:
                angle = math.pi / 2 if bit == 0 else -math.pi / 2

            self.send(self.Ports.random, FloatSignal(value=angle))
            yield self.sim_env.timeout(send_delay)
            self.send(self.Ports.trigger, TriggerSignal())
