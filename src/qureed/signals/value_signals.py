from dataclasses import dataclass
from typing import Union

from mpmath import mpf, mpc

from .generic_value_signal import GenericValueSignal


@dataclass(repr=False)
class BoolSignal(GenericValueSignal):
    """
    Boolean value carying signal

    Attributes:
    -----------
    value: bool
        The boolean value carried by the signal.
    """
    value: bool


@dataclass(repr=False)
class IntSignal(GenericValueSignal):
    """
    Integer value carying signal

    Attributes:
    -----------
    value: int
        The integer value carried by the signal.
    """
    value: int


@dataclass(repr=False)
class FloatSignal(GenericValueSignal):
    """
    Float value carying signal

    Attributes:
    -----------
    value: Union[float, mpmath.mpf]
        The float value carried by the signal. Can
        be `float` or `mpmath.mpf` for arbitrary precision.
    """
    value: Union[float, mpf]


@dataclass(repr=False)
class ComplexSignal(GenericValueSignal):
    """
    Complex value carying signal

    Attributes:
    -----------
    value: Union[float, mpmath.mpc]
        The complex value carried by the signal. Can
        be `complex` or `mpmath.mpc` for arbitrary precision.
    """
    value: Union[complex, mpc]


@dataclass(repr=False)
class StringSignal(GenericValueSignal):
    """
    String value carying signal

    Attributes:
    -----------
    value: str
        The string value carried by the signal.
    """
    value: str
