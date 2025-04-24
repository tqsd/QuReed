"""
"""

from qureed.devices import (
    GenericDevice,
    coordinate_gui,
    log_action,
    schedule_next_event,
)
from qureed.devices.port import Port
from qureed.assets import icon_list
from qureed.signals import (
    GenericBoolSignal,
    GenericIntSignal,
    GenericQuantumSignal,
    GenericSignal,
)

from qureed.extra.logging import Loggers, get_custom_logger

logger = get_custom_logger(Loggers.Custom)


class IdealDetector(GenericDevice):
    """
    Implements Ideal Single Photon Source
    """

    ports = {
        "input": Port(
            label="input",
            direction="input",
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None,
        ),
        "output": Port(
            label="output",
            direction="output",
            signal=None,
            signal_type=GenericIntSignal,
            device=None,
        ),
    }

    # Gui Configuration
    gui_icon = icon_list.DETECTOR
    gui_tags = ["ideal"]
    gui_name = "Ideal Detector"
    gui_documentation = "detector.md"

    power_peak = 0
    power_average = 0

    reference = None

    @log_action
    @schedule_next_event
    def des(self, time, *args, **kwargs):
        env = kwargs["signals"]["input"].contents
        env.fock.expand()
        outcome = env.measure()
        signal = GenericIntSignal()
        signal.set_int(outcome[env.fock])
        self.log_message(f"Measured: {outcome[env.fock]}")

        results = [("output", signal, time)]
        return results
