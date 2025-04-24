"""
Ideal Fiber Implementation
  ideal fiber has no attenuation, it just adds a delay to the signal
  the delay is proportional to the length of the fiber
"""

from typing import Union

from qureed.devices import (
    GenericDevice,
    coordinate_gui,
    log_action,
    schedule_next_event,
)
from qureed.devices.port import Port
from qureed.assets import icon_list
from qureed.signals.generic_float_signal import GenericFloatSignal
from qureed.signals.generic_int_signal import GenericIntSignal
from qureed.signals.generic_quantum_signal import GenericQuantumSignal
from qureed.simulation.constants import C


class IdealFiber(GenericDevice):
    """
    Ideal Fiber
     - no attenuation
     - only time delay
    """

    ports = {
        "length": Port(
            label="length",
            direction="input",  # Implement control
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

    def set_length(self, photon_num: int):
        """
        Set the number of photons the source should emit in a pulse
        """
        length_sig = GenericFloatSignal()
        length_sig.set_float(photon_num)
        self.register_signal(signal=length_sig, port_label="length")
        length_sig.set_computed()

    # Gui Configuration
    gui_icon = icon_list.FIBER
    gui_tags = ["ideal"]
    gui_name = "Ideal Fiber"
    gui_documentation = "ideal_fiber.md"

    power_peak = 0
    power_average = 0

    reference = None

    def __init__(self, name=None, frequency=None, time=0, uid=None, **kwargs):
        super().__init__(name=name, uid=uid)
        self.length = None


    @log_action
    @schedule_next_event
    def des(self, time, *args, **kwargs):
        signals = kwargs.get("signals")
        if self.length is None:
            if signals and "length" in signals:
                self.length = float(signals["length"].contents)
        elif signals and "input" in signals:
            n = 1.45
            # Speed of light in fiber
            v = C / n
            t = self.length / v
            #env = kwargs["signals"]["input"].contents
            signal = kwargs["signals"]["input"]
            
            result = [("output", signal, time + t)]
            return result
