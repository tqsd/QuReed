"""
Generic signal implementation,
used for defining inputs and outputs
"""
from abc import ABC, abstractmethod

class GenericSignal(ABC):  # pylint: disable=too-few-public-methods
    """
    Generic Signal class used to implement any other signal class
    """

    @abstractmethod
    def __init__(self):
        """
        Initialization method
        """

