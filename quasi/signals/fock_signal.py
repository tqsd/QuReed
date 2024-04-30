"""
Quantum Signal with Fock Modes 
"""

from quasi.signals.generic_quantum_signal import (
    GenericQuantumSignal
)


class FockSignal(GenericQuantumSignal):
    """
    Signal Carrying a reference to the Fock Mode
    """
    def __init__(self):
        super().__init__()
        self.contents = None
        self.mode_id = None
        self.timestamp = None

    def set_contents(self, timestamp, mode_id=None, content=None):
        self.mode_id = mode_id
        self.timestamp = timestamp
