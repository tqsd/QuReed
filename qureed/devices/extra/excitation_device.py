"""
Excaitation
QDCamNetz
"""
from qureed.devices import (
    GenericDevice,
    coordinate_gui,
    ensure_output_compute,
    wait_input_compute,
)
from qureed.devices.port import Port
from qureed.gui.icons import icon_list
from qureed.signals import (
    GenericBoolSignal,
    GenericFloatSignal,
    GenericQuantumSignal,
    GenericSignal,
)


class ExcitationDevice(GenericDevice):
    """
    Implements Simple Trigger,
    Trigger turns on at the start of simulation.
    """

    ports = {
        "in": Port(
            label="in",
            direction="input",
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None,
        ),
        "out1": Port(
            label="out1",
            direction="output",
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None,
        ),
        "out2": Port(
            label="out2",
            direction="output",
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None,
        ),
    }

    # Gui Configuration
    gui_icon = icon_list.EXCITATION
    gui_tags = ["extra"]
    gui_name = "Excitation"
    power = 0
    power_average = 0
    power_peak = 0
    reference = None

    @ensure_output_compute
    @coordinate_gui
    @wait_input_compute
    def compute_outputs(self, *args, **kwargs):
        pass
