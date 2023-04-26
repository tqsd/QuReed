""" Generic Device definition """
from abc import ABC, abstractmethod
from typing import Type

from quasi.signals.generic_signal import GenericSignal

class GenericDevice(ABC): # pylint: disable=too-few-public-methods
    """
    Generic Device class used to implement every device
    """
    @abstractmethod
    def __init__(self, inputs:Type[GenericSignal], outputs:Type[GenericSignal]):
        self.inputs = inputs
        self.outputs = outputs

    @abstractmethod
    def compute_outputs(self):
        """
        Computes all outputs given the inputs
        It should rise an exception if the inputs were not
        yet computed.
        """
        pass
