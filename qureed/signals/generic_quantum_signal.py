"""
Generic Quantum Signal implementation
"""

from enum import Enum, auto

from qureed.signals.generic_signal import GenericSignal


class GenericQuantumSignal(GenericSignal):
    """
    All Quantum Signals should extend this class
    """

    def __init__(self):
        super().__init__()
        self.contents = None
        self.mode_id = None
        self.timestamp = None

    def set_contents(self, content=None, timestamp=None, mode_id=None):
        self.timestamp = timestamp
        self.mode_id = mode_id
        self.contents = content
