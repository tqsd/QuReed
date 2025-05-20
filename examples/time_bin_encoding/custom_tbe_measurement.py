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
    """
        Custom Time Bin Encoding Measurement device

        This device simulates the detection and time-bin-resolved measurement
        prosecc at the end of a quantum photonic experiment. It collects photon
        detection events for each pulse and port (top/bottom) in every round,
        storing results for later statistical analysis.

        Functionality:
        --------------
        - Collects detection results for three sequential pulses ("first",
          "second", "third") for each round of the experiment.
        - For each pulse, records wether a photon was detected in the "top"
          (port `A`) or "bottom" (port `B`) detector.
        - Synchronizes measurements with an external clock signal (on `clk` port).

        Ports:
        ------
        - A (input): `QuantumOpticalPulseSignal`
            Receives `QuantumOpticalPulseSignal` for top detector.
        - B (input): `QuantumOpticalPulseSignal`
            Receives `QuantumOpticalPulseSignal` for bottom detector.

        GUI Metadata:
        -------------
        - gui_name: str
            Returns "TBE Measurement".
        - gui_icon: str
            Uses the detector icon from the asset list.

        Measurement Data Structure:
        ---------------------------
        - Measurements are stored as a list of `RoundMeasurements`, each
        containing three `Measurement` objects ("first", "second", "third")
        where each `Measurement` has:
          - top (int): 1 if photon detected at port `A`, else 0
          - bot (int): 1 if photon detected at port `B`, else 0

        Backend Compatibility:
        ----------------------
        - photon_weave: Measurement logic implemented in `proc_pw()`

        Methods:
        --------
    plot()
            Plots a histogram of the detection probabilities for each
            pulse and port (top/bottom), averaged over all rounds.

        Example:
        --------
        >>> m = TBEMeasurement()
        >>> m.set_property("name", "TBE Measurement")
        >>> # After running simulation
        >>> m.plot()
    """

    @property
    def gui_name(self) -> str:
        return "TBE Measurement"

    @property
    def gui_icon(self) -> str:
        return icon_list.DETECTOR

    # <<< type hints >>>
    class Ports(Enum):
        A = "A"
        B = "B"
        clk = "clk"

    # <<< type hints >>>

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
        """
        Clock-triggered round management process.

        Waits for a rising edge (signal) on the `clk` port to mark the end of
        a measurement round. When triggered:
        - Increments the round counter.
        - Appends the accumulated `RoundMeasurements` of the current round to
          the internal measurement list.
        - Prints the current round's measurements for debugging purposes.
        - Initializes a new, empty `RoundMEasurements` for next round.
        - Resets the pulse counter to zero ( for time bin position tracking).

        This process enables the device to separate time-resolved measurement
        results by expiremental round (e.g., for reperted trials with a clock
        or trigger pulse).

        Returns:
        --------
        None
        """
        while True:
            yield self.receive(self.Ports.clk)
            self._round += 1
            self._measurements.append(self._current_round_measurements)
            print(self._current_round_measurements)
            self._current_round_measurements = RoundMeasurements()

            self._pulse = 0

    @des_proc(backend="photon_weave")
    def proc_pw(self):
        """
        PhotonWeave backend: main pulse-resolved measurement process.

        Waits for signals on the `A` and `B` ports, which correspond to the top
        and bottom detectors of the device. On reception of at least one `END`
        type signal (indicating the end of a photon pulse):

        - Instantiates a `Measurement` object for this pulse.
        - For each received `END` signal, performs a measurement on the
          signal's payload (the quantum state) and records the detection
          outcome (0 or 1) int the `Measurement` object for appropriate port
          (top or bottom)
        - Assigns the pulse measurement to the appropriate time-bin (first,
          second, third) within the current round, based on the internal pulse
          counter.
        - Increments the pulse counter to prepare for the next detection.

        This process enables the device to accumulate time- and port-resolved
        photon detection statistics, as needed for time-bin encoding
        experiments.

        Notes:
        ------
        - Only `END` type signals are measured (i.e., actual detection events).
        - Expects that each round will have exactly three pulses per port.

        Returns:
        --------
        None

        """
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
        """
        Plots detection probabilites per time bin and port.

        Computs the average detection probability for each of the six outcomes:
        (top/.bottom x first/second/third pulse) across all measurement rounds.

        Displays a histogram with bars for:
        - Top Pulse 1, Bot Pulse 1
        - Top Pulse 2, Bot Pulse 2
        - Top Pulse 3, Bot Pulse 3

        Y-axis: Detection probability (0.0 to 1.0)
        X-axis: Pulse/port label

        Example output:
        ---------------
        |      |      |      |
        |   |  |   |  |   |  |
        |___|__|___|__|___|__|
         TP1 BP1 TP2 BP2 TP3 BP3

        Returns:
        --------
        None
        """
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
