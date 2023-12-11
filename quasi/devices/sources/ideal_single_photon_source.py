"""
Ideal Single Photon Source implementation
"""

from quasi.devices import (GenericDevice,
                           wait_input_compute,
                           ensure_output_compute)
from quasi.devices.port import Port
from quasi.signals import (GenericSignal,
                           GenericQuantumSignal)

from quasi.gui.icons import icon_list


class IdealSinglePhotonSource(GenericDevice):
    """
    Implements Ideal Single Photon Source
    """
    ports = {
        "control": Port(label="A", direction="input", signal=None,
                        signal_type=GenericSignal, device=None),
        "output": Port(label="A", direction="output", signal=None,
                       signal_type=GenericQuantumSignal, device=None),
    }

    # Gui Configuration
    gui_icon = icon_list.SINGLE_PHOTON_SOURCE
    gui_tags = ["ideal"]
    gui_name = "Ideal Single Photon Source"

    @ensure_output_compute
    @wait_input_compute
    def compute_outputs(self):
        pass
