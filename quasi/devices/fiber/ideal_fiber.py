"""
Ideal Fiber Implementation
  ideal fiber has no attenuation, it just adds a delay to the signal
  the delay is proportional to the length of the fiber
"""
from typing import Union
from quasi.devices import (GenericDevice,
                           wait_input_compute,
                           coordinate_gui,
                           ensure_output_compute)

from quasi.devices.fiber.generic_fiber import GenericFiber
from quasi.devices.port import Port
from quasi.signals.generic_float_signal import GenericFloatSignal
from quasi.signals.generic_int_signal import GenericIntSignal
from quasi.signals.generic_quantum_signal import GenericQuantumSignal
from quasi.gui.icons import icon_list
from quasi.simulation import ModeManager

class IdealFiber(GenericFiber):
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
            device=None),
        "input": Port(
            label="input",
            direction="input",
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None),
        "output": Port(
            label="output",
            direction="output",
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None),
    }

    # Gui Configuration
    gui_icon = icon_list.FIBER
    gui_tags = ["ideal"]
    gui_name = "Ideal Fiber"
    gui_documentation = "ideal_fiber.md"

    power_peak = 0
    power_average = 0

    reference = None

    
    @ensure_output_compute
    @coordinate_gui
    @wait_input_compute
    def compute_outputs(self, *args, **kwargs):
        """
        Ideal fiber only adds delay to the signal,
        without any distortions
        """
        self.ports["output"].signal.set_contents(
            timestamp=0,
            mode_id=self.ports["input"].signal.mode_id
        )
        self.ports["output"].signal.set_computed()