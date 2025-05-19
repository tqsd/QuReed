import jax.numpy as jnp
import matplotlib.pyplot as plt

from dataclasses import dataclass, field
from typing import Any, Dict
from enum import Enum
from qureed.devices.wrappers import des_proc
from qureed.signals import QuantumOpticalPulseSignal, QOPSignalType
from qureed.devices import GenericDevice
from qureed.assets import icon_list
from qureed.devices.port import Port
from qureed.signals.trigger_signal import TriggerSignal


@dataclass
class Measurement:
    top: int = -1
    bot: int = -1


@dataclass
class RoundMeasurements:
    first: Measurement = field(default_factory=Measurement)
    second: Measurement = field(default_factory=Measurement)
    third: Measurement = field(default_factory=Measurement)


class TBEMeasurement(GenericDevice):

    @property
    def gui_name(self) -> str:
        return "TBS Measuremen"

    @property
    def gui_icon(self) -> str:
        return icon_list.DETECTOR

    class Ports(Enum):
        A = "A"
        B = "B"
        clk = "clk"

    properties: Dict[str, Dict[str, Any]] = {}

    port_definitions = {
        "A": Port(direction="input", signal_type=QuantumOpticalPulseSignal),
        "B": Port(direction="input", signal_type=QuantumOpticalPulseSignal),
        "clk": Port(direction="input", signal_type=TriggerSignal),
    }

    def __init__(self, uid=None, **kwargs):
        super().__init__(uid, **kwargs)
        self._round = 0
        self._pulse = 0
        self._measurements = []
        self._current_round_measurements = RoundMeasurements()

    @des_proc
    def clk_proc(self):
        while True:
            yield self.receive(self.Ports.clk)
            self._round += 1
            self._measurements.append(self._current_round_measurements)
            print(self._current_round_measurements)
            self._current_round_measurements = RoundMeasurements()

            self._pulse = 0

    @des_proc(backend="photon_weave")
    def proc_pw(self):
        while True:
            signals = yield from self.any_receive(self.Ports.A, self.Ports.B)
            self.log(
                f"Received {len(signals)} Signals [R:{
                    self._round}, P:{self._pulse}])"
            )
            if any(s[0].type == QOPSignalType.END for s in signals):
                print("RECEIVED END")
                m = Measurement()
                for s in signals:
                    if s[0].type == QOPSignalType.END:
                        outcome = s[0].payload.measure()
                        outcome = int(outcome[s[0].payload.fock])
                        if s[1] == self.Ports.A:
                            m.top = outcome
                        if s[1] == self.Ports.B:
                            m.bot = outcome
                match self._pulse:
                    case 0:
                        self._current_round_measurements.first = m
                    case 1:
                        self._current_round_measurements.second = m
                    case 2:
                        self._current_round_measurements.third = m

                self._pulse += 1

    def plot(self):
        top_first = jnp.array([rm.first.top for rm in self._measurements])
        bot_first = jnp.array([rm.first.bot for rm in self._measurements])
        top_second = jnp.array([rm.second.top for rm in self._measurements])
        bot_second = jnp.array([rm.second.bot for rm in self._measurements])
        top_third = jnp.array([rm.third.top for rm in self._measurements])
        bot_third = jnp.array([rm.third.bot for rm in self._measurements])

        bars = [
            ("Top Pulse 1", jnp.mean(top_first)),
            ("Bot Pulse 1", jnp.mean(bot_first)),
            ("Top Pulse 2", jnp.mean(top_second)),
            ("Bot Pulse 2", jnp.mean(bot_second)),
            ("Top Pulse 3", jnp.mean(top_third)),
            ("Bot Pulse 3", jnp.mean(bot_third)),
        ]

        labels, probabilities = zip(*bars)

        plt.figure(figsize=(8, 4))
        plt.bar(labels, probabilities)
        plt.ylim(0, 1.1)
        plt.ylabel("Detection Probability")
        plt.title("Detection probability per pulse and port")
        plt.tight_layout()
        plt.show()
