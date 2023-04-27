"""
Beam Splitter
"""
from typing import Type

from quasi.devices import GenericDevice
from quasi.signals import GenericQuantumSignal


class BeamSplitter(GenericDevice):

    #Setting the class attributes
    power_average = 0
    peak_power = 0
    reference = None

    def __init__(self):
        """
        Initialization method
        """
        pass

    def register_signal(self, signal, port):
        """
        Register Signal to Port
        """
        pass
