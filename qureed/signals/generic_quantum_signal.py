from dataclasses import dataclass
from typing import Optional, Any

from .generic_signal import GenericSignal


@dataclass(repr=False)
class GenericQuantumSignal(GenericSignal):
    """
    Quantum signal container that can hold any backend-specific state
    (Fock, Gaussian, etc.).
    Attributes:
    -----------
    payload: Any
         Backend-specific quantum state container
    """

    payload: Optional[Any] = None
