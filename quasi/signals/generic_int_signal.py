"""
Generic Integer Signal implementation
"""
from quasi.signals.generic_signal import GenericSignal

class GenericIntSignal(GenericSignal):
    """
    All Quantum Signals should extend this class
    """

    def __init__(self):
        super().__init__()
        self.contents = None

    def set_int(self, x: int):
        self.contents = int(x)
