"""
Ideal Phase Shifter
"""
from quasi.devices import (GenericDevice,
                           wait_input_compute,
                           coordinate_gui,
                           ensure_output_compute)
from quasi.devices.port import Port
from quasi.signals import (GenericSignal,
                           GenericFloatSignal,
                           GenericQuantumSignal)
from quasi.extra.logging import Loggers, get_custom_logger
from quasi.gui.icons import icon_list
from quasi.simulation import Simulation, SimulationType, ModeManager

logger = get_custom_logger(Loggers.Devices)

class IdealPhaseShifter(GenericDevice):
    """
    Implements Ideal Phase Shifter
    """

    ports = {
        "theta": Port(label="theta", direction="input", signal=None,
                      signal_type=GenericFloatSignal, device=None),
        "input": Port(label="input", direction="input", signal=None,
                      signal_type=GenericQuantumSignal, device=None),
        "output": Port(label="output", direction="output", signal=None,
                       signal_type=GenericQuantumSignal, device=None)
    }

    gui_icon = icon_list.LASER
    gui_tags = ["ideal"]
    gui_name = "Ideal Coherent Photon Source"
    gui_documentation = "ideal_phase_shifter.md"

    power_peak = 0
    power_average = 0
    reference = None

    def set_phi(self, phi):
        """
        Sets the phi for the phase shifter
        """
        theta_sig = GenericFloatSignal()
        theta_sig.set_float(phi)
        self.register_signal(signal=theta_sig, port_label="theta")
        theta_sig.set_computed()

    @ensure_output_compute
    @coordinate_gui
    @wait_input_compute
    def compute_outputs(self, *args, **kwargs):
        simulation = Simulation.get_instance()
        if simulation.simulation_type is SimulationType.FOCK:
            self.simulate_fock()

    def simulate_fock(self):
        """
        Fock Simulation
        """
        logger.info("Beam Splitter - %s - executing", self.name)
        simulation = Simulation.get_instance()
        backend = simulation.get_backend()

        # Get the mode manager
        mm = ModeManager()
        # Generate new mode
        theta = self.ports["theta"].signal.contents
        mode = self.ports["input"].signal.mode_id
        logger.info("Phase Shifter - %s - received mode %s from signal on port %s",
                    self.name, mm.get_mode_index(mode),
                    self.ports["output"].label)
        
        # Initialize photon number state in the mode
        operator = backend.phase_shift(theta, mm.get_mode_index(mode))
        backend.apply_operator(operator, [mm.get_mode_index(mode)])

        logger.info("Phase Shifter - %s - assisning mode %s to signal on port %s",
                    self.name, mm.get_mode_index(mode),
                    self.ports["output"].label)

        self.ports["output"].signal.set_contents(
            timestamp=0,
            mode_id=mode)
        self.ports["output"].signal.set_computed()
