"""
Beam Splitter
"""
from quasi.devices.generic_device import GenericDevice
from quasi.devices.port import Port
from quasi.signals import GenericQuantumSignal


class BeamSplitter(GenericDevice):
    """
    Simple Beam Splitter Device
    """
    power_average = 0
    power_peak = 0
    bandwidth = 100 MHz # how do we add physical units??
    reference = {Deng21, 
                    author = {Chunyu Deng and Mengjia Lu and Yu Sun and Lei Huang and Dongyu Wang and Guohua Hu and Ruohu Zhang and Binfeng Yun and Yiping Cui},
                    journal = {Opt. Express},
                    keywords = {Coherent communications; Effective refractive index; Extinction ratios; Numerical simulation; Phase shift; Polarization splitters},
                    number = {8},
                    pages = {11627--11634},
                    publisher = {Optica Publishing Group},
                    title = {Broadband and compact polarization beam splitter in LNOI hetero-anisotropic metamaterials},
                    volume = {29},
                    month = {Apr},
                    year = {2021},
                    url = {https://opg.optica.org/oe/abstract.cfm?URI=oe-29-8-11627},
                    doi = {10.1364/OE.421262},
                }
    inputHilbertSpaces = None
    outputHilbertSpaces = None
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
