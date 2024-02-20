"""
Generic Float Signal implementation
"""
from quasi.signals.generic_signal import GenericSignal

class GenericFloatSignal(GenericSignal):
    """
    All Quantum Signals should extend this class
    """

    def __init__(self):
        super().__init__()
        self.contents = None

    def set_int(self, x: float):
        self.contents = float(x)
