"""
Generic Device definition
"""
from abc import ABC, abstractmethod
from typing import Type

from quasi.signals.generic_signal import GenericSignal

def wait_input_compute(method):
    """
    Wrapper function, makes sure that the inputs are
    computed before computing outputs.
    """
    def wrapper(self, *args, **kwargs):
        for input_signal in self.input_signals:
            input_signal.wait_till_compute()
        return method(self, *args, **kwargs)
    return wrapper


class GenericDevice(ABC): # pylint: disable=too-few-public-methods
    """
    Generic Device class used to implement every device
    """

    @abstractmethod
    def __init__(self, input_signals:Type[GenericSignal], output_signals:Type[GenericSignal]):
        """
        Initialization method
        """
        self.input_signals = input_signals
        self.output_signals = output_signals

    @wait_input_compute
    @abstractmethod
    def compute_outputs(self):
        """
        Computes all outputs given the inputs.
        Output is computed when all of the input signal (COMPUTED is set)
        """

    @property
    @abstractmethod
    def power_average(self):
        """Average Power Draw"""
        raise NotImplementedError("power must be defined")

    @property
    @abstractmethod
    def peak_power(self):
        """Peak Power Draw"""
        raise NotImplementedError("peak_power must be defined.")
