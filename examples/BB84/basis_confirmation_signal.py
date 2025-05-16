from qureed.signals import GenericSignal
from dataclasses import dataclass, field


@dataclass
class BasisConfirmSignal(GenericSignal):
    """
    Signal for basis confirmation
    """

    basis: list = field(default_factory=list)
    confirmation: list = field(default_factory=list)
