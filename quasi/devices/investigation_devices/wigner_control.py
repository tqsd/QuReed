"""
Create wigner distribution plots
"""

from quasi.devices import (GenericDevice,
                           wait_input_compute,
                           ensure_output_compute)
from quasi.devices.port import Port
from quasi.signals import (GenericSignal,
                           GenericQuantumSignal)

from quasi.gui.icons import icon_list


class WignerControl(GenericDevice):
    """
    Implements Ideal Single Photon Source
    """
    ports = {
        "input": Port(label="A", direction="input", signal=None,
                       signal_type=GenericQuantumSignal, device=None),
    }

    # Gui Configuration
    gui_icon = icon_list.WIGNER_CONTROL
    gui_tags = ["investigate"]
    gui_name = "Wigner Quasi Probability"

    @ensure_output_compute
    @wait_input_compute
    def compute_outputs(self):
        pass
