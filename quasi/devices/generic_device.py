"""
Generic Device definition
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Type
from copy import deepcopy

from quasi.simulation import Simulation, DeviceInformation


def wait_input_compute(method):
    """
    Wrapper function, makes sure that the inputs are
    computed before computing outputs.
    """
    def wrapper(self, *args, **kwargs):
        for port in self.ports.keys():
            port = self.ports[port]
            if port.direction == "input":
                if port.signal is not None:
                    port.signal.wait_till_compute()
        return method(self, *args, **kwargs)

    return wrapper


def ensure_output_compute(method):
    """
    Wrapper function, makes sure that the inputs are
    computed before computing outputs.
    TODO: write the logic
    """

    def wrapper(self, *args, **kwargs):
        return method(self, *args, **kwargs)
    return wrapper

def coordinate_gui(method):
    """
    Wrapper funciton, informs the gui about the
    status of the simulation
    """
    def wrapper(self, *args, **kwargs):
        if self.coordinator is not None:
            self.coordinator.start_processing()
        method(self, *args, **kwargs)
        if self.coordinator is not None:
            self.coordinator.processing_finished()

    return wrapper




class GenericDevice(ABC):  # pylint: disable=too-few-public-methods
    """
    Generic Device class used to implement every device
    """

    def __init__(self, name=None, uid=None):
        """
        Initialization method
        """
        self.name = name
        self.ports = deepcopy(self.__class__.ports)
        if hasattr(self.__class__, "values"):
            self.values = deepcopy(self.__class__.values)
        for port in self.ports.keys():
            self.ports[port].device = self


        # Regitering the device to the simulation
        print(f"NEW DEVICE {uid}")
        simulation = Simulation.get_instance()
        ref = DeviceInformation(name=name, obj_ref=self, uid=uid)
        self.ref = ref
        simulation.register_device(ref)
        self.coordinator = None
        

    def register_signal(
        self, signal: GenericSignal, port_label: str, override: bool = False
    ):
        """
        Register a signal to port
        """
        port = None
        try:
            port = self.ports[port_label]
        except KeyError as exc:
            raise NoPortException(
                f"Port with label {port_label} does not exist."
            ) from exc

        if not port.signal is None:
            if not override:
                raise PortConnectedException(
                    "Signal was already registered for the port\n"
                    + "If this is intended, set override to True"
                )

        if not (
            isinstance(signal, port.signal_type)
            or issubclass(type(signal), port.signal_type)
        ):
            raise PortSignalMismatchException()

        signal.register_port(port, self)
        port.signal = signal

    @wait_input_compute
    @coordinate_gui
    @abstractmethod
    def compute_outputs(self):
        """
        Computes all outputs given the inputs.
        Output is computed when all of the input signal (COMPUTED is set)
        """


    @property
    @abstractmethod
    def ports(self) -> Dict[str, Type["Port"]]:
        """Average Power Draw"""
        raise NotImplementedError("power must be defined")

    @property
    @abstractmethod
    def power_average(self):
        """Average Power Draw"""
        raise NotImplementedError("power must be defined")

    @property
    @abstractmethod
    def power_peak(self):
        """Peak Power Draw"""
        raise NotImplementedError("peak_power must be defined.")

    @property
    @abstractmethod
    def reference(self):
        """
        Reference is used to compile references for specific
        experiment.
        """
        raise NotImplementedError("Can be set to None")

    def set_coordinator(self, coordinator):
        """
        Sets the coordinator
        this is required to have feedback in the gui
        """
        self.coordinator = coordinator
        


class NoPortException(Exception):
    """
    Raised when port, which should be accessed doesn't exist
    """


class PortConnectedException(Exception):
    """
    Raised when Signal is already registered for the port.
    """


class PortSignalMismatchException(Exception):
    """
    Raised when signal doesn't match the port description
    """
