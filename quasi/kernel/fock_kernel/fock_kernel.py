"""
This module implements a Fock Kernel
"""
from typing import List
from quasi.kernel.generic_kernel import GenericKernel


class FockMode():
    """
    Just holds information about fock mode
    """
    def __init__(self, truncation):
        self.truncation = truncation

class FockState():
    """
    This class keeps track of the modes
    """
    def __init__(self, fock_mode: FockMode):
        self.modified = True
        pass

    def cleanup(self):
        if self.modified:
            pass

class FockKernel(GenericKernel):
    """
    This class implements Fock Kernel,
    Fock Kernel allows modes to have varied truncations.
    """
    def __init__(self):
        """
        According to the special issue
        """
        self.state = []
        self.modes = []

    def add_mode(self, truncation: int):  # pylint: disable=arguments-differ
        """
        Creates a new mode in vaccum state and returns the index of the mode
        """
        fm = FockMode(truncation)
        self.modes.append(fm)
        self.state.append(FockState(fm))


    def _cleanup(self):
        """
        Determines if the modes could be split
        """

    def remove_mode(self, mode_index:int):  # pylint: disable=arguments-differ
        pass

