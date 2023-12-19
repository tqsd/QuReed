"""
Int Variable
"""
from quasi.devices import (GenericDevice,
                           wait_input_compute,
                           coordinate_gui,
                           ensure_output_compute)
from quasi.devices.port import Port
from quasi.signals import GenericIntSignal

from quasi.gui.icons import icon_list


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
            device=None),
    }

    # Gui Configuration
    gui_icon = icon_list.SIMPLE_TRIGGER
    gui_tags = ["variable", "integer"]
    gui_name = "Int Variable"
    power = 0
    power_average = 0
    power_peak = 0
    reference = None

    values = {
        "value": None
    }

    @ensure_output_compute
    @coordinate_gui
    @wait_input_compute
    def compute_outputs(self, *args, **kwargs):
        self.ports["int"].signal.set_int(self.values["value"])
        self.ports["int"].signal.set_computed()


    def set_value(self, value:str):
        self.values["value"] = int(value)
