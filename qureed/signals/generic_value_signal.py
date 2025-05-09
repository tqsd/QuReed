from dataclasses import dataclass
from typing import Any

from .generic_signal import GenericSignal

@dataclass
class GenericValueSignal(GenericSignal):
    """
    Abstract base class for classigal signals that carry a typed value.

    Attributes:
    -----------
    value: Any
        The value this signal carries.
    """
    value: Any = None

    def __repr__(self):
        return f"<{self.__class__.__name__} ts={self.timestamp} val={self.value} metadata={self.metadata}>"
