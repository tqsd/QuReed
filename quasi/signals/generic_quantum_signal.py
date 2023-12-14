"""
Generic Quantum Signal implementation
"""
from enum import Enum, auto

from quasi.signals.generic_signal import GenericSignal


class QuantumContentType(Enum):
    NONE = -1
    FOCK = auto()
    QOPS = auto()


class GenericQuantumSignal(GenericSignal):
    """
    All Quantum Signals should extend this class
    """

    def __init__(self):
        super().__init__()
        self.contents = None
        self.content_type = QuantumContentType.NONE

    def set_contents(self, content_type:QuantumContentType, content):
        self.content_type = content_type
