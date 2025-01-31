"""
Generic Quantum Signal implementation
"""

from qureed.signals.generic_signal import GenericSignal


class GenericStringSignal(GenericSignal):
    """
    All Quantum Signals should extend this class
    """

    def __init__(self):
        super().__init__()
        self.contents = None

    def set_bool(self, b: str):
        self.contents = b
