"""
t
Simulation Module
"""

import simpy

from qureed.backends import _BACKENDS, UnknownBackendException


class Simulation:
    """
    Simulation (Singleton)

    Handles the simulation process.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Simulation, cls).__new__(cls)
        return cls._instance

    def __init__(self, backend="photon_weave"):
        if not hasattr(self, "initialized"):
            self.simpy_env = simpy.Environment()
            if backend not in _BACKENDS:
                raise UnknownBackendException(
                    f"Backend is not known. Registered backends: {_BACKENDS}"
                )
            self._backend = backend
            self.initialized = True

    @property
    def backend(self) -> str:
        return self._backend

    @backend.setter
    def backend(self, backend: str) -> None:
        if backend not in _BACKENDS:
            raise UnknownBackendException(
                f"Backend is not known. Registered backends: {_BACKENDS}"
            )
        self._backend = backend

    def run(self, *args, **kwargs):
        self.simpy_env.run(*args, **kwargs)

    @classmethod
    def reset(cls):
        """
        Reset the singleton instance for test isolation.
        """
        cls._instance = None
