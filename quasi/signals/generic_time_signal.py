"""
Generic Time Signal Implementation
"""

from quasi.signals.generic_signal import GenericSignal


class GenericTimeSignal(GenericSignal):
    def __init__(self):
        super().__init__()
        self.contents = None

    def set_time(self, time: float):
        self.contents = time
