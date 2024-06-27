from qureed.devices import (
    GenericDevice,
    wait_input_compute,
    coordinate_gui,
    ensure_output_compute,
)
from qureed.devices.port import Port
from qureed.signals import GenericSignal, GenericFloatSignal, GenericQuantumSignal
from qureed.extra.logging import Loggers, get_custom_logger
from qureed.gui.icons import icon_list
from qureed.simulation import Simulation, SimulationType, ModeManager

logger = get_custom_logger(Loggers.Devices)


class CustomPhaseShift(GenericDevice):
    """
    Implements Ideal Phase Shifter
    """

    ports = {
        "voltage": Port(
            label="voltage",
            direction="input",
            signal=None,
            signal_type=GenericFloatSignal,
            device=None,
        ),
        "A": Port(
            label="A",
            direction="input",
            signal=None,
            signal_type=GenericFloatSignal,
            device=None,
        ),
        "B": Port(
            label="B",
            direction="input",
            signal=None,
            signal_type=GenericFloatSignal,
            device=None,
        ),
        "C": Port(
            label="C",
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

    gui_icon = icon_list.LASER
    gui_tags = ["ideal"]
    gui_name = "Ideal Coherent Photon Source"
    gui_documentation = "ideal_phase_shifter.md"

    power_peak = 0
    power_average = 0
    reference = None

    def set_params(self, voltage, A, B, C):
        """
        Sets the phi for the phase shifter
        """
        sig_voltage = GenericFloatSignal()
        sig_voltage.set_float(voltage)
        self.register_signal(signal=sig_voltage, port_label="voltage")
        sig_voltage.set_computed()

        sig_A = GenericFloatSignal()
        sig_A.set_float(A)
        self.register_signal(signal=sig_A, port_label="A")
        sig_A.set_computed()

        sig_B = GenericFloatSignal()
        sig_B.set_float(B)
        self.register_signal(signal=sig_B, port_label="B")
        sig_B.set_computed()

        sig_C = GenericFloatSignal()
        sig_C.set_float(C)
        self.register_signal(signal=sig_C, port_label="C")
        sig_C.set_computed()

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
        mode = self.ports["input"].signal.mode_id
        voltage = self.ports["voltage"].signal.contents
        A = self.ports["A"].signal.contents
        B = self.ports["B"].signal.contents
        C = self.ports["C"].signal.contents

        phi = A * voltage**B + C

        # Initialize photon number state in the mode
        operator = backend.phase_shift(phi, mm.get_mode_index(mode))
        backend.apply_operator(operator, [mm.get_mode_index(mode)])

        logger.info(
            "Phase Shifter - %s - assisning mode %s to signal on port %s",
            self.name,
            mm.get_mode_index(mode),
            self.ports["output"].label,
        )

        self.ports["output"].signal.set_contents(timestamp=0, mode_id=mode)
        self.ports["output"].signal.set_computed()
