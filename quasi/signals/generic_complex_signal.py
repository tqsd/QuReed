"""
Generic Float Signal implementation
"""
from quasi.signals.generic_signal import GenericSignal

class GenericComplexSignal(GenericSignal):
    """
    All Quantum Signals should extend this class
    """

    def __init__(self):
        super().__init__()
        self.contents = None

    def set_complex(self, x: complex):
        """
        Sets the content to the specified float
        """
        self.contents = complex(x)
