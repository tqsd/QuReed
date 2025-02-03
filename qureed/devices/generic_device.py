"""
Generic Device definition
"""

from __future__ import annotations

import functools
from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Dict, Type

from qureed.devices.port import Port
from qureed.extra import Loggers, get_custom_logger
from qureed.signals.generic_signal import GenericSignal
from qureed.simulation import DeviceInformation, Simulation

type_mapping = {
    "int": int,
    "float": float,
    "bool": bool,
    "cmplx": complex,
    "str": str,
    "char": lambda v: v if len(v) == 1 else ValueError("Value must be a single character")
}


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
        l.info(formatted_message)
        return method(self, time, *args, **kwargs)

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
                l.info(formatted_message)
                signals = {port: signal}
                self.simulation.schedule_event(time, next_device, signals=signals)

    return wrapper


class GenericDevice(ABC):  # pylint: disable=too-few-public-methods
    """
    Generic Device class used to implement every device
    """

    properties = {
        "name":{
            "type": str,
             }
        }

    def __init__(self, uid=None, **kwargs):
        """
        Initialization method
        """
        self.ports = deepcopy(self.__class__.ports)
        #self.properties = deepcopy(self.__class__.properties)
        self.properties = deepcopy(self._merge_properties())
        print("All properties", self.properties)
        for port in self.ports.keys():
            self.ports[port].device = self

        simulation = Simulation.get_instance()
        ref = DeviceInformation(obj_ref=self, uid=uid)
        self.ref = ref
        simulation.register_device(ref)
        self.coordinator = None
        self.simulation = Simulation.get_instance()

    def _merge_properties(self):
        """
        Merge properties from the base class and the subclass.
        """
        combined_properties = deepcopy(GenericDevice.properties)
        print(combined_properties)
        subclass_properties = getattr(self.__class__, "properties", {})
        print(subclass_properties)
        combined_properties.update(subclass_properties)  # Subclass properties override or add to parent
        return combined_properties

    def set_property(self, property_name, value):
        print(self.properties[property_name]["type"])
        print(type(self.properties[property_name]["type"]))
        if not property_name in self.properties.keys():
            raise AttributeError(f"{self.__class__.__name__} has no property {property_name}")
        if not isinstance(value, self.properties[property_name]["type"]):
            raise TypeError(f"{property_name} Expected {self.properties[property_name]['type']}, got {type(value)}")
        self.properties[property_name]["value"] = value

    def get_property(self, property_name):
        if not property_name in self.properties.keys():
            raise AttributeError(f"{self.__class__.__name__} has no property {property_name}")
        return self.properties[property_name].get("value",None)
        

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
                    + f"Device: {type(self)}, {self.properties['name']['value']}, {self.ref.uuid}\n"
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

    @property
    @abstractmethod
    def ports(self) -> Dict[str, Type["Port"]]:
        """Average Power Draw"""
        raise NotImplementedError("power must be defined")

    @property
    @abstractmethod
    def gui_name(self):
        """Gui name"""
        raise NotImplementedError("gui_name must be defined")

    @property
    @abstractmethod
    def gui_icon(self):
        """Gui name"""
        raise NotImplementedError("gui_icon must be defined")

    @property
    @abstractmethod
    def reference(self):
        """
        Reference is used to compile references for specific
        experiment.
        """
        raise NotImplementedError(
            "reference can be set to None, but must be implemented"
        )

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
            raise DESActionNotDefined("Either des or des_action method must be defined")

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
