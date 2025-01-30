"""
Ideal Single Photon Source implementation
"""
import numpy as np
from photon_weave.state.envelope import Envelope

from qureed.devices import (
    GenericDevice,
    coordinate_gui,
    log_action,
    schedule_next_event,
)
from qureed.devices.port import Port
from qureed.extra.logging import Loggers, get_custom_logger
from qureed.assets import icon_list
from qureed.signals import (
    GenericBoolSignal,
    GenericIntSignal,
    GenericQuantumSignal,
    GenericSignal,
)
from qureed.simulation import Simulation, SimulationType

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
            device=None,
        ),
        "photon_num": Port(
            label="photon_num",
            direction="input",
            signal=None,
            signal_type=GenericIntSignal,
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
        elif "trigger" in kwargs["signals"] and self.photon_num is not None:
            n = int(self.photon_num)
            # Creating new envelope
            env = Envelope()
            env.fock.state = n
            # Creating output
            signal = GenericQuantumSignal()
            signal.set_contents(content=env)
            result = [("output", signal, time)]
            return result
        else:
            raise Exception("Unknown Photon Num")
