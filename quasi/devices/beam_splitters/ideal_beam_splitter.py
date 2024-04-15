"""
Ideal Beam Splitter implementation
"""

from quasi.devices import (GenericDevice,
                           schedule_next_event,
                           log_action,
                           wait_input_compute,
                           ensure_output_compute)
from quasi.devices.port import Port
from quasi.signals import (GenericSignal,
                           GenericQuantumSignal)
from math import pi

from quasi.gui.icons import icon_list
from quasi.simulation import Simulation, SimulationType, ModeManager
from quasi.extra.logging import Loggers, get_custom_logger
from photon_weave.state.envelope import Envelope

logger = get_custom_logger(Loggers.Devices)

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

    def __init__(self, name=None, uid=None):
        super().__init__(name=name, uid=uid)


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

        # Utilize a helper function to streamline mode ID retrieval or creation
        def get_or_create_mode_id(port):
            if port.signal is None:
                logger.info("Beam Splitter - %s - empty signal, new mode generated", self.name)
                return mm.create_new_mode()
            return port.signal.mode_id

        m_id_a = get_or_create_mode_id(self.ports["B"])
        m_id_b = get_or_create_mode_id(self.ports["A"])

        # Apply beam splitter operation in a more concise manner
        op = backend.beam_splitter(theta=pi/4, phi=pi/2)
        backend.apply_operator(op, [mm.get_mode_index(m_id_a),
                                    mm.get_mode_index(m_id_b)])

        # Simplify signal content setting using a loop to avoid repetition
        for port, mode_id in zip(
                [self.ports["C"], self.ports["D"]], [m_id_a, m_id_b]):
            if port.signal is not None:
                logger.info("Beam Splitter - %s - assisning mode %s to signal on port %s",
                            self.name, mm.get_mode_index(mode_id), port.label)
                port.signal.set_contents(timestamp=0, mode_id=mode_id)
                port.signal.set_computed()


    @log_action
    @schedule_next_event
    def des_action(self, time=None, *args, **kwargs):
        print("BEAMSPLITTER")
        


    def compute_overlap(self, env1:Envelope, env2:Envelope):
        """
        Computes overlap for two photons
        """
