"""
Ideal Fiber
"""

from quasi.devices.generic_device import GenericDevice
from quasi.devices.generic_device import wait_input_compute
from quasi.devices.generic_device import ensure_output_compute
from quasi.extra import Reference
from quasi.signals import GenericQuantumSignal
from quasi.devices.port import Port



class IdealFiber(GenericDevice):
    """
    Ideal Beam Fiber Device
    Just transferrs the inputs to the outputs
    """
    power_average = 0
    power_peak = 0
    reference = None
    ports = {
        "IN": Port(label="B", direction="input",signal=None,
                  signal_type=GenericQuantumSignal, device=None),
        "OUT": Port(label="D", direction="output",signal=None,
                  signal_type=GenericQuantumSignal, device=None),
    }

    def __init__(self, length ,  wavelength=1550, name=None):
        super().__init__(name)
        self.wavelength = wavelength

    @ensure_output_compute
    @wait_input_compute
    def compute_outputs(self):
        """
        Waits for the input singlas to be computed
        and then the outputs are computed by this method
        """
