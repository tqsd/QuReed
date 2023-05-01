"""
Beam Splitter
"""
from quasi.devices.generic_device import GenericDevice
from quasi.devices.generic_device import wait_input_compute
from quasi.devices.generic_device import ensure_output_compute
from quasi.devices.port import Port
from quasi.signals import GenericQuantumSignal
from quasi.extra import Reference


_BEAM_SPLITTER_BIB= {
    "author" : "Chunyu Deng and Mengjia Lu and Yu Sun and Lei Huang and"\
    "Dongyu Wang and Guohua Hu and Ruohu Zhang and Binfeng Yun and Yiping Cui",
    "journal": "Opt. Express" ,
    "keywords": "Coherent communications; Effective refractive index;"\
    " Extinction ratios; Numerical simulation; Phase shift; Polarization splitters",
    "number":8,
    "pages":"11627--11634",
    "publisher":"Optica Publishing Group",
    "title": "Broadband and compact polarization beam splitter in LNOI;"\
    " hetero-anisotropic metamaterials",
    "volume":29,
    "month":"Apr",
    "year":2021,
    "url": "https://opg.optica.org/oe/abstract.cfm?URI=oe-29-8-11627",
    "doi": "10.1364/OE.421262"
}
_BEAM_SPLITTER_DOI= "10.1364/OE.421262"

class BeamSplitter(GenericDevice):
    """
    Simple Beam Splitter Device
    """
    power_average = 0
    power_peak = 0
    reference = Reference(doi=_BEAM_SPLITTER_DOI, bib_dict=_BEAM_SPLITTER_BIB)

    #bandwidth = 100 MHz # how do we add physical units??
    # We could implement some logic to store the phisical parameters for devices
    # However I propose that for example in this case we should specify the
    # values in the Signal class
    # In this case we could account for devices of varying complexity


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
    def compute_outpus(self):
        """
        Here the output signals should be computed.
        ---
        @wait_input_compute guarantees, that the signals at input ports
        are calculated.
        @ensure_output_compute raises an exception if compute has finished,
        but output signals compute flag was not set.
        """
