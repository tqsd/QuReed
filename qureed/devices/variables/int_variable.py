"""
Int Variable
"""
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
from qureed.signals import GenericIntSignal
from qureed.simulation import Simulation


class IntVariable(GenericDevice):
    """
    Implements integer variable setter
    """

    ports = {
        "int": Port(
            label="int",
            direction="output",
            signal=None,
            signal_type=GenericIntSignal,
            device=None,
        ),
    }

    # Gui Configuration
    gui_icon = icon_list.SIMPLE_TRIGGER
    gui_tags = ["variable", "integer"]
    gui_name = "Int Variable"
    power = 0
    power_average = 0
    power_peak = 0
    reference = None

    def __init__(self, name=None, time=-1, uid=None):
        super().__init__(name=name, uid=uid)
        self.time = time
        self.simulation = Simulation.get_instance()
        self.simulation.schedule_event(time, self)

    values = {"value": None}

    @ensure_output_compute
    @coordinate_gui
    @wait_input_compute
    def compute_outputs(self, *args, **kwargs):
        self.ports["int"].signal.set_int(self.values["value"])
        self.ports["int"].signal.set_computed()

    def set_value(self, value: str):
        self.values["value"] = int(value)

    @log_action
    @schedule_next_event
    def des(self, time, *args, **kwargs):
        signal = GenericIntSignal()
        signal.set_int(int(self.values["value"]))
        result = [("int", signal, time + 0)]
        return result

    @log_action
    @schedule_next_event
    def des_action(self, time=None, *args, **kwargs):
        next_device, port = self.get_next_device_and_port("int")
        signal = GenericIntSignal()
        signal.set_int(int(self.values["value"]))
        result = [("int", signal, self.time)]
        return result
