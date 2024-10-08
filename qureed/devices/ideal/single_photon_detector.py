"""
Ideal Single Photon Source
"""
from qureed.devices.generic_device import (
    GenericDevice,
    ensure_output_compute,
    wait_input_compute,
)
from qureed.devices.port import Port
from qureed.extra import Reference
from qureed.signals import GenericQuantumSignal


class IdealSinglePhotonDetector(GenericDevice):
    """
    Ideal Single Photon Emitter
    """

    ports = {
        "IN": Port(
            label="D",
            direction="input",
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None,
        ),
    }

    reference = None
    power_average = 1
    power_peak = 1

    def __init__(self, wavelength=1550, name=None):
        super().__init__(name)
        self.wavelength = wavelength

    @ensure_output_compute
    @wait_input_compute
    def compute_outputs(self):
        """
        Waits for the input singlas to be computed
        and then the outputs are computed by this method
        """
        pass
