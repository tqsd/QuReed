"""
Simple Trigger
"""
from quasi.devices import (GenericDevice,
                           wait_input_compute,
                           ensure_output_compute)
from quasi.devices.port import Port
from quasi.signals import (GenericSignal,
                           GenericBoolSignal,
                           GenericQuantumSignal)

from quasi.gui.icons import icon_list


class SimpleTrigger(GenericDevice):
    """
    Implements Simple Trigger,
    Trigger turns on at the start of simulation.
    """
    ports = {
        "T": Port(label="T",
                  direction="output",
                  signal=None,
                  signal_type=GenericBoolSignal,
                  device=None),
    }

    # Gui Configuration
    gui_icon = icon_list.SIMPLE_TRIGGER
    gui_tags = ["control"]
    gui_name = "Simple Trigger"
    power = 0
    power_average = 0
    power_peak = 0
    reference = None

    @ensure_output_compute
    @wait_input_compute
    def compute_outputs(self, *args, **kwargs):
        print("TRIGGERING")
        self.ports["T"].data = True
        self.ports["T"].signal.set_computed()

