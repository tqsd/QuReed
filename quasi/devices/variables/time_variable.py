"""
Float Variable
"""

from quasi.devices import (
    GenericDevice,
    wait_input_compute,
    coordinate_gui,
    ensure_output_compute,
    log_action,
    schedule_next_event,
)
from quasi.devices.port import Port
from quasi.signals import GenericTimeSignal

from quasi.gui.icons import icon_list


class TimeVariable(GenericDevice):
    """
    Implements integer variable setter
    """

    ports = {
        "time": Port(
            label="time",
            direction="output",
            signal=None,
            signal_type=GenericTimeSignal,
            device=None,
        ),
    }

    # Gui Configuration
    gui_icon = icon_list.SIMPLE_TRIGGER
    gui_tags = ["variable", "time"]
    gui_name = "Time Variable"
    power = 0
    power_average = 0
    power_peak = 0
    reference = None

    values = {"value": None}

    def __init__(self, name=None, uid=None):
        super().__init__(name=name, uid=uid)
        self.simulation.schedule_event(-1, self)

    @ensure_output_compute
    @coordinate_gui
    @wait_input_compute
    def compute_outputs(self, *args, **kwargs):
        self.ports["time"].signal.set_time(self.values["value"])
        self.ports["time"].signal.set_computed()

    def set_value(self, value: str):
        if value is "":
            self.values["time"] = float(0)
        else:
            self.values["time"] = float(value)

    @log_action
    @schedule_next_event
    def des_action(self, time=None, *args, **kwargs):
        signal = GenericTimeSignal()
        signal.set_time(self.values["time"])
        result = [("time", signal, time)]
        return result
