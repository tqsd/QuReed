""" Generic Device definition """
from abc import ABC, abstractmethod

class GenericDevice(ABC):
    """
    Generic Device class used to implement every device
    """

    @abstractmethod
    def compute_outputs(self):
        """
        Computes all outputs given the inputs
        It should rise an exception if the inputs were not
        yet computed.
        """
        pass
