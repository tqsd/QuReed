from abc import ABC
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass(kw_only=True)
class GenericSignal(ABC):
    """
    Base class for all signal types in QuReed

    This class can be extended to create specific signal types,
    such as optical, quantum, or classical signals

    Attributes:
    -----------
    timestamp: Optional(float)
        The time (in simulation units) when the signal is created or sent.
    sender: Any
        The device or process that generated this signal
    metadata : Dict[str, Any]
        Arbitrary extra data attached to the signal
    terminate : bool
        If True, the signal will not propagate
    """

    timestamp: Optional[float] = None
    sender: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    terminate: bool = False

    def __repr__(self):
        return (
            f"<{self.__class__.__name__} "
            f"ts={self.timestamp} "
            f"metadata={self.metadata}>"
        )
