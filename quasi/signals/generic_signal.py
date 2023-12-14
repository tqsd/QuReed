"""
Generic Signal implementation,
used for defining inputs and outputs
"""
from abc import ABC
from threading import Event



class GenericSignal(ABC):  # pylint: disable=too-few-public-methods
    """
    Generic Signal class used to implement any other signal class
    """

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

    def wait_till_compute(self, timeout=None):
        """
        Blocking call, waits until the signal is computed
        """
        self.computed.wait(timeout)

    def register_port(self, port: Port):
        """
        Registers the port to the signal
        """
