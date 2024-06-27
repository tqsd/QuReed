"""
Ideal Phase Shifter
"""

from photon_weave.operation.fock_operation import FockOperation, FockOperationType

from qureed.devices import (
    GenericDevice,
    coordinate_gui,
    ensure_output_compute,
    log_action,
    schedule_next_event,
    wait_input_compute,
)
from qureed.devices.port import Port
from qureed.extra.logging import Loggers, get_custom_logger
from qureed.gui.icons import icon_list
from qureed.signals import GenericFloatSignal, GenericQuantumSignal, GenericSignal
from qureed.simulation import ModeManager, Simulation, SimulationType

logger = get_custom_logger(Loggers.Devices)


class IdealPhaseShifter(GenericDevice):
    """
    Implements Ideal Phase Shifter
    """

    ports = {
        "theta": Port(
            label="theta",
            direction="input",
            signal=None,
            signal_type=GenericFloatSignal,
            device=None,
        ),
        "input": Port(
            label="input",
            direction="input",
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None,
        ),
        "output": Port(
            label="output",
            direction="output",
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None,
        ),
    }

    gui_icon = icon_list.PHASE_SHIFT
    gui_tags = ["ideal"]
    gui_name = "Ideal Phase Shifter"
    gui_documentation = "ideal_phase_shifter.md"

    power_peak = 0
    power_average = 0
    reference = None

    def __init__(self, name=None, time=0, uid=None):
        super().__init__(name=name, uid=uid)
        self.theta = 0

    def set_theta(self, theta):
        """
        Sets the phi for the phase shifter
        """
        theta_sig = GenericFloatSignal()
        theta_sig.set_float(theta)
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
        logger.info(
            "Phase Shifter - %s - received mode %s from signal on port %s",
            self.name,
            mm.get_mode_index(mode),
            self.ports["output"].label,
        )

        # Initialize photon number state in the mode
        operator = backend.phase_shift(theta, mm.get_mode_index(mode))
        backend.apply_operator(operator, [mm.get_mode_index(mode)])

        logger.info(
            "Phase Shifter - %s - assisning mode %s to signal on port %s",
            self.name,
            mm.get_mode_index(mode),
            self.ports["output"].label,
        )

        self.ports["output"].signal.set_contents(timestamp=0, mode_id=mode)
        self.ports["output"].signal.set_computed()

    @log_action
    @schedule_next_event
    def des(self, time=None, *args, **kwargs):
        if "theta" in kwargs.get("signals"):
            self.theta = kwargs["signals"]["theta"].contents
        if "input" in kwargs.get("signals"):
            env = kwargs["signals"]["input"].contents
            fo = FockOperation(FockOperationType.PhaseShift, phi=self.theta)
            env.apply_operation(fo)
            signal = GenericQuantumSignal()
            signal.set_contents(env)
            result = [("output", signal, time)]
            return result
