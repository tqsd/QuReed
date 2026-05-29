from dataclasses import dataclass

from .generic_signal import GenericSignal


@dataclass(repr=False)
class TriggerSignal(GenericSignal):
    """
    Trigger Signal, does not contain any payload
    """

    def __repr__(self) -> str:
        return "<TriggerSignal>"
