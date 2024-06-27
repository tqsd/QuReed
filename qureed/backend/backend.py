"""
This module implements the Backend Feature.
"""

from abc import ABC, abstractmethod
from typing import List


class Backend(ABC):
    """
    All Backends are singletons
    """

    _instances = {}

    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Backend, cls).__new__(cls)
        return cls._instances[cls]


class FockBackend(Backend):
    """
    This class enforces the structure of the Fock Backends
    """

    @abstractmethod
    def set_number_of_modes(self, number_of_modes):
        """
        Tells the backend number of modes that should be simulated
        """

    @abstractmethod
    def create(self, mode):
        """
        Should return creation operator
        """

    @abstractmethod
    def destroy(self, mode):
        """
        Should return annihilation method
        """

    @abstractmethod
    def squeeze(self, z: complex, mode):
        """
        Should return squeezing operator
        """

    @abstractmethod
    def displace(self, alpha: float, phi: float, mode):
        """
        Should return displacement operator
        """

    @abstractmethod
    def phase_shift(self, theta: float, mode):
        """
        Should return phase shift operator
        """

    @abstractmethod
    def number(self, mode):
        """
        Should return number operator
        """

    @abstractmethod
    def apply_operator(self, operator, modes: List[int]):
        """
        Should Apply the operator to the correct mode
        """
