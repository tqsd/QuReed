"""
Ideal Beam Splitter
"""

from quasi.devices.generic_device import GenericDevice




class BeamSplitter(GenericDevice):
    """
    Ideal Beam Splitter Device
    """

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
