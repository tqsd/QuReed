"""
Generic signal implementation,
used for defining inputs and outputs
"""
from abc import ABC, abstractmethod

class GenericSignal(ABC):
    """
    Generic Signal class used to implement any other signal class
    """

    @abstractmethod
    def __init__(self):

    @abstractmethod
    def dummy(self):
        """
        Dummy method to appease the linters.
        """
