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
from qureed.signals import GenericBoolSignal, GenericQuantumSignal
from qureed.simulation import Simulation, SimulationType

_SINGLE_PHOTON_SOURCE_BIB = {
    "title": '{"u}ber eine verbesserung der wienschen spektralgleichung',
    "author": "Planck, Max",
    "year": "1978",
    "publisher": "Springer",
}

_SINGLE_PHOTON_SOURCE_DOI = "10.1007/978-3-663-13885-3_15"


class IdealSinglePhotonSource(GenericDevice):
    """
    Ideal Single Photon Emitter
    """

    ports = {
        "TRIGGER": Port(
            label="A",
            direction="input",
            signal=None,
            signal_type=GenericBoolSignal,
            device=None,
        ),
        "OUT": Port(
            label="A",
            direction="output",
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None,
        ),
    }

    reference = Reference(
        doi=_SINGLE_PHOTON_SOURCE_DOI, bib_dict=_SINGLE_PHOTON_SOURCE_BIB
    )
    power_average = 1
    power_peak = 1

    def __init__(self, wavelength=1550, name=None):
        super().__init__(name)
        self.wavelength = wavelength
        self.simulation = Simulation.get_instance()

    @ensure_output_compute
    @wait_input_compute
    def compute_outputs(self):
        """
        Method router
          Based on the simulation type and received signal we
          select the method which computes the outputs
        """
        # ROUTERS NEED TO BE IMPLEMENTED
        if self.simulation.simulation_type == SimulationType.FOCK:
            self.fock()

    def fock(self):
        pass
