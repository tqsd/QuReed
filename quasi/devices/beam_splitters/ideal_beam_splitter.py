"""
Ideal Beam Splitter implementation
"""

from quasi.devices import (GenericDevice,
                           wait_input_compute,
                           ensure_output_compute)
from quasi.devices.port import Port
from quasi.signals import (GenericSignal,
                           GenericQuantumSignal)
from math import pi

from quasi.gui.icons import icon_list
from quasi.simulation import Simulation, SimulationType, ModeManager


class IdealBeamSplitter(GenericDevice):
    """
    Implements Ideal Single Photon Source
    """
    ports = {
        "A": Port(label="A", direction="input", signal=None,
                  signal_type=GenericQuantumSignal, device=None),
        "B": Port(label="B", direction="input", signal=None,
                  signal_type=GenericQuantumSignal, device=None),
        "C": Port(label="C", direction="output", signal=None,
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
        simulation = Simulation.get_instance()
        if simulation.simulation_type is SimulationType.FOCK:
            self.simulate_fock()
        

    def simulate_fock(self):
        """
        Fock Simulation
        """
        simulation = Simulation.get_instance()
        backend = simulation.get_backend()
        mm = ModeManager()
        m_id_a = self.ports["A"].signal.mode_id
        m_id_b = self.ports["B"].signal.mode_id

        op = backend.beam_splitter(theta=pi/4, phi=0)
        backend.apply_operator(
            op,
            [mm.get_mode_index(m_id_a),
             mm.get_mode_index(m_id_b)]
        )

        # Get the modes or create empty modes
        m_id_a = self.ports["A"].signal.mode_id
        m_id_b = self.ports["B"].signal.mode_id

