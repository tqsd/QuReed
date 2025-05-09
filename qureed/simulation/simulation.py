"""
Simulation Module
"""

# pylint: skip-file
import traceback
import sys
import heapq
import uuid
from dataclasses import dataclass
from enum import Enum, auto
from threading import Thread
from typing import TYPE_CHECKING, Type

import mpmath
import simpy


from qureed.backends import _BACKENDS, UnknownBackendException
from qureed.extra import (
    Loggers,
    get_custom_logger,
    set_logging_hook,
    set_simulation
    )

if TYPE_CHECKING:
    from qureed.devices import GenericDevice


class Simulation:
    """
    Simulation (Singleton)

    Handles the simulation process.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Simulation, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, backend="photon_weave"):
        if not hasattr(self, "initialized"):
            self.simpy_env = simpy.Environment()
            if backend not in _BACKENDS:
                raise UnknownBackendException(
                    f"Backend is not known. Registered backends: {_BACKENDS}"
                    )
            self.backend=backend
            self.initialized = True

    def run(self, *args, **kwargs):
        self.simpy_env.run(*args, **kwargs)
