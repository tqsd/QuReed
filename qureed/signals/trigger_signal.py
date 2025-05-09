from dataclasses import dataclass

from .generic_signal import GenericSignal

@dataclass(repr=False)
class TriggerSignal(GenericSignal):
    """
    Quantum signal container that can hold any backend-specific state
    (Fock, Gaussian, etc.).
    Attributes:
    -----------
    payload: Any
         Backend-specific quantum state container
    """
