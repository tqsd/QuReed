"""
Simple Trigger
: DES Tested
"""

from quasi.devices import (
    GenericDevice,
    wait_input_compute,
    coordinate_gui,
    log_action,
    schedule_next_event,
    ensure_output_compute,
)
from quasi.devices.port import Port
from quasi.signals import GenericBoolSignal, GenericTimeSignal
from quasi.simulation import Simulation

from quasi.gui.icons import icon_list
from quasi.extra import Loggers, get_custom_logger


class SimpleTrigger(GenericDevice):
    """
    Implements Simple Trigger,
    Trigger turns on at the start of simulation.
    """

    ports = {
        "time": Port(
            label="time",
            direction="input",
            signal=None,
            signal_type=GenericTimeSignal,
            device=None,
        ),
        "trigger": Port(
            label="trigger",
            direction="output",
            signal=None,
            signal_type=GenericBoolSignal,
            device=None,
        ),
    }

    # Gui Configuration
    gui_icon = icon_list.SIMPLE_TRIGGER
    gui_tags = ["control"]
    gui_name = "Simple Trigger"
    power = 0
    power_average = 0
    power_peak = 0
    reference = None

    def __init__(self, name=None, time=0, uid=None):
        super().__init__(name=name, uid=uid)
        self.time = time
        self.simulation = Simulation.get_instance()
        self.simulation.schedule_event(0, self)

    @ensure_output_compute
    @coordinate_gui
    @wait_input_compute
    def compute_outputs(self, *args, **kwargs):
        self.ports["trigger"].signal.set_bool(True)
        self.ports["trigger"].signal.set_computed()

    @log_action
    @schedule_next_event
    def des_action(self, time=None, *args, **kwargs):
        if self.time is None:
            next_device, port = self.get_next_device_and_port("trigger")
            signal = GenericBoolSignal()
            signal.set_bool(True)
            result = [("trigger", signal, self.time)]
            return result

    @log_action
    @schedule_next_event
    def des(self, time=None, *args, **kwargs):
        if "time" in kwargs.get("signals"):
            self.time = kwargs["signals"]["time"].contents
            self.simulation.schedule_event(self.time, self)
        if (self.time is None and time == 0) or time == self.time:
            signal = GenericBoolSignal()
            signal.set_bool(True)
            result = [("trigger", signal, self.time)]
            return result
