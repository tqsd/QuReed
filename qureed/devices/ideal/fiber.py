"""
Ideal Fiber
"""

from qureed.devices.generic_device import (
    GenericDevice,
    ensure_output_compute,
    wait_input_compute,
)
from qureed.devices.port import Port
from qureed.extra import Reference
from qureed.signals import GenericQuantumSignal


class IdealFiber(GenericDevice):
    """
    Ideal Beam Fiber Device
    Just transferrs the inputs to the outputs
    """

    power_average = 0
    power_peak = 0
    reference = None
    ports = {
        "IN": Port(
            label="B",
            direction="input",
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None,
        ),
        "OUT": Port(
            label="D",
            direction="output",
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None,
        ),
    }

    def __init__(self, length, wavelength=1550, name=None):
        super().__init__(name)
        self.wavelength = wavelength

    @ensure_output_compute
    @wait_input_compute
    def compute_outputs(self):
        """
        Waits for the input singlas to be computed
        and then the outputs are computed by this method
        """
        print("FIBER RECEIVED SOMETHING")
        self.ports["OUT"].signal.set_computed()
