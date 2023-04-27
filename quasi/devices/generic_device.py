""" Generic Device definition """
from abc import ABC, abstractmethod
from typing import Type
from multiprocessing import Event

from quasi.signals.generic_signal import GenericSignal

def wait_input_compute(fn):
    """
    Wrapper function, makes sure that the inputs are
    computed before computing outputs.
    """
    def wrapper(self):
        for input in self.inputs:
            input.wait_till_compute()
    return wrapper


class GenericDevice(ABC): # pylint: disable=too-few-public-methods
    """
    Generic Device class used to implement every device
    """


    @abstractmethod
    def __init__(self, inputs:Type[GenericSignal], outputs:Type[GenericSignal]):
        self.inputs = inputs
        self.outputs = outputs

    @wait_input_compute
    @abstractmethod
    def compute_outputs(self):
        """
        Computes all outputs given the inputs.
        Output is computed when all of the input signal (COMPUTED is set)
        """

    @property
    @abstractmethod
    def POWER_AVERAGE(cls):
        """Average Power Draw"""
        raise NotImplementedError("POWER must be defined. It can be 0.")

    @property
    @abstractmethod
    def POWER_PEAK(cls):
        """Peak Power Draw"""
        raise NotImplementedError("POWER must be defined. It can be 0.")
