"""
Clock Trigger
"""
from quasi.devices import (GenericDevice,
                           wait_input_compute,
                           coordinate_gui,
                           ensure_output_compute)
from quasi.devices.port import Port
from quasi.signals import (GenericSignal,
                           GenericFloatSignal,
                           GenericBoolSignal,
                           GenericQuantumSignal)

from quasi.gui.icons import icon_list


class ClockTrigger(GenericDevice):
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
        "frequency": Port(
            label="frequency",
            direction="input",
            signal=None,
            signal_type=GenericFloatSignal,
            device=None),

    }

    # Gui Configuration
    gui_icon = icon_list.CLOCK_TRIGGER
    gui_tags = ["control"]
    gui_name = "Clock Trigger"
    power = 0
    power_average = 0
    power_peak = 0
    reference = None

    @ensure_output_compute
    @coordinate_gui
    @wait_input_compute
    def compute_outputs(self, *args, **kwargs):
        """
        Reimplement this,
        This component is a currently implemented as a visual
        demo only.
        """
        self.ports["T"].signal.set_bool(True)
        self.ports["T"].signal.set_computed()
