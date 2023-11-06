"""
Generic Device definition
"""
from abc import ABC, abstractmethod
from typing import Dict
from copy import deepcopy


from quasi.signals.generic_signal import GenericSignal
from quasi.devices.port import Port


def wait_input_compute(method):
    """
    Wrapper function, makes sure that the inputs are
    computed before computing outputs.
    """

    def wrapper(self, *args, **kwargs):
        for port in self.ports:
            if port.direction == "input":
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


class GenericDevice(ABC):  # pylint: disable=too-few-public-methods
    """
    Generic Device class used to implement every device
    """

    def __init__(self):
        """
        Initialization method
        """
        self.ports = deepcopy(self.__class__.ports)
        for port in self.ports:
            port.device = self

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

        signal.register_port(port)
        port.signal = signal

    @wait_input_compute
    @abstractmethod
    def compute_outputs(self):
        """
        Computes all outputs given the inputs.
        Output is computed when all of the input signal (COMPUTED is set)
        """

    @property
    @abstractmethod
    def ports(self) -> Dict[str, Port]:
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
