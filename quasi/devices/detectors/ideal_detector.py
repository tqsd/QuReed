"""
"""

import numpy as np

from quasi.devices import (
    GenericDevice,
    wait_input_compute,
    log_action,
    schedule_next_event,
    coordinate_gui,
    ensure_output_compute,
)
from quasi.devices.port import Port
from quasi.signals import (
    GenericSignal,
    GenericBoolSignal,
    GenericIntSignal,
    GenericQuantumSignal,
)

from quasi.gui.icons import icon_list
from quasi.simulation import ModeManager

from quasi._math.fock.ops import adagger, a


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
