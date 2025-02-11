"""
Ideal Phase Shifter
"""


from qureed.devices import (
    GenericDevice,
    coordinate_gui,
    log_action,
    schedule_next_event,
)

from qureed.devices.port import Port
from qureed.extra.logging import Loggers, get_custom_logger
from qureed.assets import icon_list
from qureed.signals import GenericFloatSignal, GenericQuantumSignal, GenericSignal
from qureed.simulation import Simulation, SimulationType

from photon_weave.operation import Operation, FockOperationType

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

    def __init__(self, name=None, time=0, uid=None, **kwargs):
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

    @log_action
    @schedule_next_event
    def des(self, time=None, *args, **kwargs):
        if "theta" in kwargs.get("signals"):
            self.theta = kwargs["signals"]["theta"].contents
        if "input" in kwargs.get("signals"):
            env = kwargs["signals"]["input"].contents
            fo = Operation(FockOperationType.PhaseShift, phi=self.theta)
            env.fock.apply_operation(fo)
            signal = GenericQuantumSignal()
            signal.set_contents(env)
            result = [("output", signal, time)]
            return result
