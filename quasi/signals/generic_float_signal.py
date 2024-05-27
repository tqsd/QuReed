"""
Generic Float Signal implementation
"""
from quasi.signals.generic_signal import GenericSignal
from quasi.signals.generic_complex_signal import GenericComplexSignal

class GenericFloatSignal(GenericComplexSignal):
    """
    All Quantum Signals should extend this class
    """

    def __init__(self):
        super().__init__()
        self.contents = None

    def set_float(self, x: float):
        """
        Sets the content to the specified float
        """
        self.contents = float(x)
