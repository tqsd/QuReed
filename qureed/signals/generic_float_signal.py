"""
Generic Float Signal implementation
"""
from qureed.signals.generic_complex_signal import GenericComplexSignal
from qureed.signals.generic_signal import GenericSignal


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
