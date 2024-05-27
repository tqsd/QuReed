"""
Generic Device definition
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Type
from copy import deepcopy
import functools

from quasi.simulation import Simulation, DeviceInformation
from quasi.extra import Loggers, get_custom_logger
from quasi.signals.generic_signal import GenericSignal
from quasi.devices.port import Port
from quasi.simulation import ModeManager


def log_action(method):
    @functools.wraps(method)
    def wrapper(self, time, *args, **kwargs):
        # Convert mpf to float for formatting
        l = get_custom_logger(Loggers.Devices)
        time_as_float = float(time)
        # Correctly format the string before passing to l.info
        if self.name is not None:
            formatted_message = "[{:-3e}s] *{}* ({}) is computing".format(
                time_as_float, self.name, self.__class__.__name__
            )
        else:
            formatted_message = "[{:.3e}s] {} is computing".format(
                time_as_float, self.__class__.__name__
            )

        # Now, pass the formatted_message to the log
        # print(formatted_message)
        l.info(formatted_message)
        return method(self, time, *args, **kwargs)

    return wrapper


def wait_input_compute(method):
    """
    Wrapper function, makes sure that the inputs are
    computed before computing outputs.
    """

    @functools.wraps(method)
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

    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        return method(self, *args, **kwargs)

    return wrapper


def coordinate_gui(method):
    """
    Wrapper funciton, informs the gui about the
    status of the simulation
    """

    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if self.coordinator is not None:
            self.coordinator.start_processing()
        x = method(self, *args, **kwargs)
        if self.coordinator is not None:
            self.coordinator.processing_finished()
        return x

    return wrapper


def schedule_next_event(method):
    """
    Schedules the next device event, if it exists
    """

    @functools.wraps(method)
    def wrapper(self, time, *args, **kwargs):
        results = method(self, time, *args, **kwargs)
        if results is None:
            return
        for output_port, signal, time in results:
            next_device, port = self.get_next_device_and_port(output_port)
            if not next_device is None:
                time_as_float = float(time)
                l = get_custom_logger(Loggers.Devices)
                if self.name is None:
                    if next_device.name is None:
                        formatted_message = (
                            "<{:.3e}s> {} is scheduling new event for {}".format(
                                time_as_float,
                                self.__class__.__name__,
                                next_device.__class__.__name__,
                                time_as_float,
                            )
                        )
                    else:
                        formatted_message = (
                            "<{:.3e}s> {} is scheduling new event for {} ({})".format(
                                time_as_float,
                                self.__class__.__name__,
                                next_device.name,
                                next_device.__class__.__name__,
                                time_as_float,
                            )
                        )
                else:
                    formatted_message = (
                        "<{:.3e}s> {} ({}) is scheduling new event for {} ({})".format(
                            time_as_float,
                            self.name,
                            self.__class__.__name__,
                            next_device.name,
                            next_device.__class__.__name__,
                            time_as_float,
                        )
                    )
                # print(formatted_message)
                l.info(formatted_message)
                signals = {port: signal}
                self.simulation.schedule_event(time, next_device, signals=signals)

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

        simulation = Simulation.get_instance()
        ref = DeviceInformation(name=name, obj_ref=self, uid=uid)
        self.ref = ref
        simulation.register_device(ref)
        self.coordinator = None
        self.simulation = Simulation.get_instance()

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

        if port.signal is not None:
            if not override:
                raise PortConnectedException(
                    f"Signal was already registered for the port\n"
                    + "If this is intended, set override to True\n"
                    + f"Device: {type(self)}, {self.name}, {self.ref.uuid}\n"
                    + f"Port: {type(port.signal)}, {port_label}"
                )

        if not (
            isinstance(signal, port.signal_type)
            or issubclass(type(signal), port.signal_type)
        ):
            raise PortSignalMismatchException(
                "This port does not support selected signal"
            )

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

    @log_action
    def des(self, time, *args, **kwargs):
        if hasattr(self, "envelope_backend"):
            self.envelope_backend(*args, **kwargs)
        elif hasattr(self, "des_action"):
            self.des_action(time, *args, **kwargs)
        else:
            raise DESActionNotDefined()

    def get_next_device_and_port(self, port: str):
        port = self.ports[port]
        if port.signal:
            for connected_port in port.signal.ports:
                if connected_port != port:
                    return connected_port.device, connected_port.label
        return None, None


class DESActionNotDefined(Exception):
    """
    Raised when device should be called with des simulation,
    but des methods are not defined
    """


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
