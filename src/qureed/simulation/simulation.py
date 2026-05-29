from __future__ import annotations
from typing import List, TYPE_CHECKING, Optional
import simpy

from qureed.backends import _BACKENDS, UnknownBackendException

if TYPE_CHECKING:
    from examples.BB84.custom_fiber import GenericDevice
    from qureed.devices.connection import Connection


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
            self.devices: List["GenericDevice"] = []
            self.connections: List["Connection"] = []

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

    def register_device(self, device: GenericDevice):
        self.devices.append(device)

    def enable_logging(
        self, *, name_contains: str | None = None, all: bool = False
    ) -> None:
        """
        Turn on logging for devices.

        Parameters
        ----------
        name_contains : str, optional
            Substring (case‐insensitive) to match against:
            - device.gui_name
            - device class name
            - device.properties['name'].value
        all : bool
            If True, enable logging on *all* devices (ignores name_contains).
        """
        if all:
            for d in self.devices:
                d.logging = True
            return

        if not name_contains:
            return

        key = name_contains.lower()
        for d in self.devices:
            # gui_name or class name
            gui = d.gui_name.lower()
            cls = d.__class__.__name__.lower()

            # explicit "name" property value if present
            val = ""
            try:
                val = str(d.properties["name"]["value"]).lower()
            except Exception:
                pass

            if key in gui or key in cls or key in val:
                d.logging = True
