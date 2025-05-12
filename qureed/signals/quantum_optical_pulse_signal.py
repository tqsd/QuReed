from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional, Tuple, Dict
from enum import StrEnum

from .generic_quantum_signal import GenericQuantumSignal


class QOPSignalType(StrEnum):
    START = "start"
    END = "end"


@dataclass(kw_only=True)
class QuantumOpticalPulseSignal(GenericQuantumSignal):
    """
    A quantum optical signal that represents a time-localized quantum event,
    such as a photon pulse.

    Each signal is either a `START` or `END ` marker and is designed to appear
    in matched pairs.
    Both signals in the pair share the same payload and are linked through the
    `pair` attribute.

    Inherited Attributes:
    ---------------------
    payload : Any
        Backend-specific quantum state container. Shared between the START and
        END signals.

    Attributes:
    -----------
    type: QOPSignalType
        Indicates whether this signal marks the start or end of the pulse.
    pair: Optional[QuantumPulseSignal]
        A reference to the corresponding signal in the pair. Set automatically
        by `create_pair()`

    Usage Example:
    --------------
    >>> from qureed.signals import QuantumOpticalPulseSignal
    >>>
    >>> payload = "Backend Specific Payload"
    >>> start, end = QuantumOpticalPulseSignal.create_pair(payload)
    """

    type: QOPSignalType
    pair: Optional[QuantumOpticalPulseSignal] = None

    @classmethod
    def create_pair(
        cls, payload: Any, metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple["QuantumOpticalPulseSignal", "QuantumOpticalPulseSignal"]:
        """
        Create a pair of QuantumOpticalPulseSignal instances with matching
        payloads and cross-references.

        This thod is the canonical way to instantiate START/END signal pairs
        that are temporally and logically linked. Both signals will point to
        each other through their `pair` attributes.

        Arguments:
        ----------
        payload: Any
            The backend-specific quantum state or data to attach to both
            signals.
        metadata: Optional[Dict[str, Any]]
            Optional metadata.

        Returns:
        --------
        Tuple[QuantumOpticalPulseSignal, QuantumOpticalPulseSignal]
            A tuple containing the START and END signals.
        """
        start = cls(type=QOPSignalType.START, payload=payload)
        end = cls(type=QOPSignalType.END, payload=payload)
        if metadata:
            start.metadata = metadata
            end.metadata = metadata
        start.pair = end
        end.pair = start
        return start, end
