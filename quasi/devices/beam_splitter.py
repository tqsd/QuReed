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
    reference = None
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
