"""
This module implements a Generic Kernel.
Generic Kernel enforces structure in the kernels.
"""

from abc import ABCMeta, abstractmethod

class SingletonMeta(ABCMeta):
    """
    All kernels must be singletons
    """
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class GenericKernel(metaclass=SingletonMeta):
    """
    Enforcing Structure for the Kernels.
    All kernels must extend this class
    """

    @abstractmethod
    def add_mode(self, *args, **kwargs):
        pass

    @abstractmethod
    def remove_mode(self, *args, **kwargs):
        pass
