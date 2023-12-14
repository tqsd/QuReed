"""
Ideal Beam Splitter implementation
"""

from quasi.devices import (GenericDevice,
                           wait_input_compute,
                           ensure_output_compute)
from quasi.devices.port import Port
from quasi.signals import (GenericSignal,
                           GenericQuantumSignal)

from quasi.gui.icons import icon_list


class IdealBeamSplitter(GenericDevice):
    """
    Implements Ideal Single Photon Source
    """
    ports = {
        "A": Port(label="A", direction="input", signal=None,
                  signal_type=GenericSignal, device=None),
        "B": Port(label="B", direction="output", signal=None,
                  signal_type=GenericQuantumSignal, device=None),
        "C": Port(label="C", direction="input", signal=None,
                  signal_type=GenericSignal, device=None),
        "D": Port(label="D", direction="output", signal=None,
                  signal_type=GenericQuantumSignal, device=None),
    }

    # Gui Configuration
    gui_icon = icon_list.BEAM_SPLITTER
    gui_tags = ["ideal"]
    gui_name = "Ideal Beam Splitter"

    @wait_input_compute
    def compute_outputs(self):
        print("TEST")
