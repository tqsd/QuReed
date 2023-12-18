"""
Ideal Beam Splitter implementation
"""

from quasi.devices import (GenericDevice,
                           wait_input_compute,
                           ensure_output_compute)
from quasi.devices.port import Port
from quasi.signals import (GenericSignal,
                           QuantumContentType,
                           GenericQuantumSignal)

from quasi.gui.icons import icon_list
from quasi.simulation import ModeManager


class IdealBeamSplitter(GenericDevice):
    """
    Implements Ideal Single Photon Source
    """
    ports = {
        "A": Port(label="A", direction="input", signal=None,
                  signal_type=GenericQuantumSignal, device=None),
        "B": Port(label="B", direction="output", signal=None,
                  signal_type=GenericQuantumSignal, device=None),
        "C": Port(label="C", direction="input", signal=None,
                  signal_type=GenericQuantumSignal, device=None),
        "D": Port(label="D", direction="output", signal=None,
                  signal_type=GenericQuantumSignal, device=None),
    }

    # Gui Configuration
    gui_icon = icon_list.BEAM_SPLITTER
    gui_tags = ["ideal"]
    gui_name = "Ideal Beam Splitter"
    gui_documentation = "ideal_beam_splitter.md"

    power_average = 0
    power_peak = 0
    reference = None
    
    @wait_input_compute
    def compute_outputs(self,  *args, **kwargs):
        mm = ModeManager()

        m_id_a = self.ports["A"].signal.mode_id
        m_id_b = self.ports["B"].signal.mode_id

        self.ports["C"].signal.set_contents(
            content_type=QuantumContentType.FOCK,
            mode_id=m_id_a)

        self.ports["D"].signal.set_contents(
            content_type=QuantumContentType.FOCK,
            mode_id=m_id_b)
        print(mm.modes.keys())

        self.ports["C"].signal.set_computed()
        self.ports["D"].signal.set_computed()
