"""
Generic Quantum Signal implementation
"""

from qureed.signals.generic_signal import GenericSignal


class GenericBoolSignal(GenericSignal):
    """
    All Quantum Signals should extend this class
    """

    def __init__(self):
        super().__init__()
        self.contents = None

    def set_bool(self, b: bool):
        self.contents = b
