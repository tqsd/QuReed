"""
Ideal Fiber
"""

from quasi.devices.generic_device import GenericDevice
from quasi.devices.generic_device import wait_input_compute
from quasi.devices.generic_device import ensure_output_compute
from quasi.extra import Reference
from quasi.signals import GenericQuantumSignal




class Fiber(GenericDevice):
    """
    Ideal Beam Fiber Device
    Just transferrs the inputs to the outputs
    """

    ports = {
        "IN": Port(label="B", direction="input",signal=None,
                  signal_type=GenericQuantumSignal, device=None),
        "OUT": Port(label="D", direction="output",signal=None,
                  signal_type=GenericQuantumSignal, device=None),
    }

    @ensure_output_compute
    @wait_input_compute
    def compute_outputs(self):
        """
        Waits for the input singlas to be computed
        and then the outputs are computed by this method
        """
        pass
