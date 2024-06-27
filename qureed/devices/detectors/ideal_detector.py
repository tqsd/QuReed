"""
"""

import numpy as np

from qureed._math.fock.ops import a, adagger
from qureed.devices import (
    GenericDevice,
    coordinate_gui,
    ensure_output_compute,
    log_action,
    schedule_next_event,
    wait_input_compute,
)
from qureed.devices.port import Port
from qureed.gui.icons import icon_list
from qureed.signals import (
    GenericBoolSignal,
    GenericIntSignal,
    GenericQuantumSignal,
    GenericSignal,
)
from qureed.simulation import ModeManager


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

    @ensure_output_compute
    @coordinate_gui
    @wait_input_compute
    def compute_outputs(self, *args, **kwargs):
        pass

    @log_action
    @schedule_next_event
    def des(self, time, *args, **kwargs):
        env = kwargs["signals"]["input"].contents
        ce = env.composite_envelope
        print(ce.states[0][0])
        outcome = ce.measure(env)
        signal = GenericIntSignal()
        print(outcome)
        signal.set_int(outcome[0])

        results = [("output", signal, time)]
        return results
