"""
Ideal Single Photon Source implementation
"""
import numpy as np

from quasi.devices import (GenericDevice,
                           wait_input_compute,
                           coordinate_gui,
                           schedule_next_event,
                           log_action,
                           ensure_output_compute)
from quasi.devices.port import Port
from quasi.signals import (GenericSignal,
                           GenericBoolSignal,
                           GenericIntSignal,
                           GenericQuantumSignal)

from quasi.gui.icons import icon_list
from quasi.simulation import Simulation, SimulationType, ModeManager
from quasi.experiment import Experiment
from quasi.extra.logging import Loggers, get_custom_logger
from quasi.backend.envelope_backend import EnvelopeBackend
from photon_weave.state.envelope import Envelope
from photon_weave.operation.fock_operation import(
    FockOperation, FockOperationType
)

logger = get_custom_logger(Loggers.Devices)


class IdealNPhotonSource(GenericDevice):
    """
    Implements Ideal Single Photon Source
    """
    ports = {
        "trigger": Port(
            label="trigger",
            direction="input",
            signal=None,
            signal_type=GenericBoolSignal,
            device=None),
        "photon_num": Port(
            label="photon_num",
            direction="input",
            signal=None,
            signal_type=GenericIntSignal,
            device=None),
        "output": Port(
            label="output",
            direction="output",
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None),
    }

    # Gui Configuration
    gui_icon = icon_list.N_PHOTON_SOURCE
    gui_tags = ["ideal"]
    gui_name = "Ideal N Photon Source"
    gui_documentation = "ideal_n_photon_source.md"

    power_peak = 0
    power_average = 0
    reference = None

    def __init__(self, name=None, time=0, uid=None):
        super().__init__(name=name, uid=uid)
        self.photon_num = None

    def set_photon_num(self, photon_num: int):
        """
        Set the number of photons the source should emit in a pulse
        """
        photon_num_sig = GenericIntSignal()
        photon_num_sig.set_int(photon_num)
        self.register_signal(signal=photon_num_sig, port_label="photon_num")
        photon_num_sig.set_computed()
    

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
        simulation = Simulation.get_instance()
        backend = simulation.get_backend()

        # Get the mode manager
        mm = ModeManager()
        # Generate new mode
        mode = mm.create_new_mode()
        # How many photons should be created
        photon_num = self.ports["photon_num"].signal.contents
        
        # Initialize photon number state in the mode
        backend.initialize_number_state(photon_num, [mm.get_mode_index(mode)])

        logger.info(
            "Source - %s - assisning mode %s to signal on port %s",
            self.name, mm.get_mode_index(mode),
            self.ports["output"].label)
        self.ports["output"].signal.set_contents(
            timestamp=0,
            mode_id=mode)
        self.ports["output"].signal.set_computed()

    def set_photon_num(self, photon_num: int):
        """
        Set the number of photons the source should emit in a pulse
        """
        self.photon_num = photon_num

    @coordinate_gui
    @schedule_next_event
    @log_action
    def des(self, time, *args, **kwargs):
        if "photon_num" in kwargs["signals"]:
            self.set_photon_num(float(kwargs["signals"]["photon_num"].contents))
        if "trigger" in kwargs["signals"] and self.photon_num is not None:
            n = self.photon_num
            # Creating new envelopt
            env = Envelope()
            # Applying operation
            op = FockOperation(FockOperationType.Creation, apply_count=n)
            env.apply_operation(op)
            # Creating output
            signal = GenericQuantumSignal()
            signal.set_contents(content=env)
            result = [("output", signal, time)]
            return result
        else:
            raise Exception("Unknown Photon Num")
