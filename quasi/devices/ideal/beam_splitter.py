"""
Ideal Beam Splitter
"""

from quasi.devices.generic_device import GenericDevice
from quasi.devices.generic_device import wait_input_compute
from quasi.devices.generic_device import ensure_output_compute
from quasi.extra import Reference
from quasi.signals import GenericQuantumSignal


_BEAM_SPLITTER_BIB = {
  "title":"Quantum theory of the lossless beam splitter",
  "author":"Fearn, H and Loudon, R",
  "journal":"Optics communications",
  "volume":64,
  "number":6,
  "pages":"485--490",
  "year":1987,
  "publisher"="Elsevier"
}

_BEAM_SPLITTER_DOI = "https://doi.org/10.1016/0030-4018(87)90275-6"



class BeamSplitter(GenericDevice):
    """
    Ideal Beam Splitter Device
    """

    reference = Reference(doi=_BEAM_SPLITTER_DOI, bib_dict=_BEAM_SPLITTER_BIB)

    ports = {
        "A": Port(label="A", direction="input",signal=None,
                  signal_type=GenericQuantumSignal, device=None),
        "B": Port(label="B", direction="input",signal=None,
                  signal_type=GenericQuantumSignal, device=None),
        "C": Port(label="C", direction="output",signal=None,
                  signal_type=GenericQuantumSignal, device=None),
        "D": Port(label="D", direction="output",signal=None,
                  signal_type=GenericQuantumSignal, device=None),
    }

    @ensure_output_compute
    @wait_input_compute
    def compute_outputs(self):
        """
        Waits for the input singlas to be computed
        and then the outputs are computed by this method
        """
