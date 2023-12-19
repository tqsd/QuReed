"""
Float Variable
"""
from quasi.devices import (GenericDevice,
                           wait_input_compute,
                           coordinate_gui,
                           ensure_output_compute)
from quasi.devices.port import Port
from quasi.signals import GenericFloatSignal

from quasi.gui.icons import icon_list


class FloatVariable(GenericDevice):
    """
    Implements integer variable setter
    """
    ports = {
        "float": Port(
            label="float",
            direction="output",
            signal=None,
            signal_type=GenericFloatSignal,
            device=None),
    }

    # Gui Configuration
    gui_icon = icon_list.SIMPLE_TRIGGER
    gui_tags = ["variable", "float"]
    gui_name = "Float Variable"
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
        self.values["value"] = float(value)
