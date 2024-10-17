"""

 created with template
"""
from typing import Union
from qureed.devices import (
    GenericDevice,
    wait_input_compute,
    schedule_next_event,
    coordinate_gui,
    log_action,
    ensure_output_compute,
)

from qureed.devices.port import Port
from qureed.simulation import ModeManager
from qureed.signals import *


class CustomFilter(GenericDevice):
    ports = {
        "input": Port(
            label="input",
            direction="input",
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None,
        ),
        "exciton": Port(
            label="exciton",
            direction="output",  # Changed from "input" to "output" for clarity
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None,
        ),
        "biexciton": Port(
            label="biexciton",
            direction="output",  # Changed from "input" to "output" for clarity
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None,
        ),
    }

    gui_icon = None
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
        s = kwargs["signals"]["input"]
        env = s.contents
        if env.wavelength < 825:
            return [("exciton", s, time)]
        return [("biexciton", s, time)]

    @log_action
    @schedule_next_event
    def des_action(self, time=None, *args, **kwargs):
        """
        Or implement this if you are implementing a trigger
        """
        pass
