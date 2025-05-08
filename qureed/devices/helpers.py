from __future__ import annotations
from enum import Enum

from .exceptions import PortSignalMismatchException

def common_signal_type(cls1, cls2):
    for base in cls1.__mro__:
        if issubclass(cls2, base):
            return base
    raise PortSignalMismatchException(
        f"No ccommon signal base between {cls1.__name__} and {cls2.__name__}"
        )

def normalize_port(port: str | Enum) -> str:
    return port.value if isinstance(port, Enum) else port

