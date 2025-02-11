"""
Ideal Coherent Source Implementation
"""

from math import factorial

from qureed.devices import (
    GenericDevice,
    coordinate_gui,
    log_action,
    schedule_next_event,
)
from qureed.devices.port import Port
from qureed.assets import icon_list
from qureed.signals import (
    GenericBoolSignal,
    GenericFloatSignal,
    GenericQuantumSignal,
    GenericSignal,
)

from qureed.simulation import Simulation, SimulationType

from photon_weave.state.envelope import Envelope
from photon_weave.operation import Operation, FockOperationType


class IdealCoherentSource(GenericDevice):
    """
    COHERENT
    """

    ports = {
        "trigger": Port(
            label="trigger",
            direction="input",
            signal=None,
            signal_type=GenericBoolSignal,
            device=None,
        ),
        "alpha": Port(
            label="alpha",
            direction="input",
            signal=None,
            signal_type=GenericFloatSignal,
            device=None,
        ),
        "phi": Port(
            label="phi",
            direction="input",
            signal=None,
            signal_type=GenericFloatSignal,
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

    # Gui Configuration
    gui_icon = icon_list.LASER
    gui_tags = ["ideal"]
    gui_name = "Ideal Coherent Photon Source"
    gui_documentation = "ideal_coherent_photon_source.md"

    power_peak = 0
    power_average = 0

    reference = None

    def __init__(self, name=None, frequency=None, time=0, uid=None, **kwargs):
        super().__init__(name=name, uid=uid)
        self.alpha = None
        self.phi = None

    def set_displacement(self, alpha: float, phi: float):
        """
        Sets the signals so that the source correctly displaces the vacuum
        """
        alpha_sig = GenericFloatSignal()
        alpha_sig.set_float(alpha)
        phi_sig = GenericFloatSignal()
        phi_sig.set_float(phi)
        self.register_signal(signal=alpha_sig, port_label="alpha")
        self.register_signal(signal=phi_sig, port_label="phi")
        phi_sig.set_computed()
        alpha_sig.set_computed()

    @coordinate_gui
    @schedule_next_event
    @log_action
    def des(self, time, *args, **kwargs):
        signals = kwargs.get("signals")
        if "alpha" in signals or "phi" in signals:
            self._extract_parameters(kwargs)
        if "trigger" in signals:
            if self.alpha is None:
                raise Exception("Alpha not provided")
            if signals["trigger"].contents:
                env = Envelope()
                op = Operation(FockOperationType.Displace, alpha=self.alpha)
                env.fock.apply_operation(op)
                signal = GenericQuantumSignal()
                signal.set_contents(content=env)
                result = [("output", signal, time)]
                return result

    def _extract_parameters(self, kwargs):
        signals = kwargs.get("signals")
        if signals and "alpha" in signals:
            self.alpha = signals["alpha"].contents
        if signals and "phi" in signals:
            self.phi = signals["phi"].contents
