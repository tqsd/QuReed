"""
Generic signal implementation,
used for defining inputs and outputs
"""
from abc import ABC, abstractmethod
from multiprocessing import Event


class GenericSignal(ABC):  # pylint: disable=too-few-public-methods
    """
    Generic Signal class used to implement any other signal class
    """

    @abstractmethod
    def __init__(self):
        """
        Initialization method
        """
        self.computed = Event()

    def set_computed(self):
        """
        After signal is computed the computed flag should be set
        """
        self.computed.set()

    def wait_till_compute(self, timeout=-1):
        """
        Blocking call, waits until the signal is computed
        """
        self.computed.wait(timeout=timeout)
