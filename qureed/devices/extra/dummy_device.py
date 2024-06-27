"""

 created with template
"""
from typing import Union

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
from qureed.signals import *
from qureed.simulation import ModeManager


class DummyDevice(GenericDevice):
    ports = {
        "input": Port(
            label="input",
            direction="input",
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None,
        ),
        "control": Port(
            label="control",
            direction="input",
            signal=None,
            signal_type=GenericBoolSignal,
            device=None,
        ),
        "output": Port(
            label="output",
            direction="output",  # Changed from "input" to "output" for clarity
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None,
        ),
    }

    gui_name = "Dummy Device"
    gui_icon = icon_list.PHASE_SHIFT
    gui_tags = None
    gui_documentation = None

    power_peak = 0
    power_average = 0

    reference = None

    @ensure_output_compute
    @coordinate_gui
    @wait_input_compute
    def compute_outputs(self, *args, **kwargs):
        """
        Implement to use the regular backend
        """
        pass

    @log_action
    @schedule_next_event
    def des(self, time, *args, **kwargs):
        """
        Implement to use discrete event simulation
        """
        pass

    @log_action
    @schedule_next_event
    def des_action(self, time=None, *args, **kwargs):
        """
        Or implement this if you are implementing a trigger
        """
        pass
