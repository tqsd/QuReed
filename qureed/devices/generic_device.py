from __future__ import annotations

"""
Defines the abstract base class `GenericDevice`, which provides a reusable
template for all SimPy-based quantum or classical devices.

This class includes:
- Port definition handling via a metaclass
- Connection validation and management
- Signal routing via `send`, `receive`, and `deliver`
- Property handling and simulation environment registration

To implement a custom device, inherit from `GenericDevice` and define:
- `port_definitions`: A dictionary of labeled ports
- `gui_name` and `gui_icon`: GUI metadata
- (Optionally) `reference`: For documentation or citation
"""

import inspect
import types
import uuid
from abc import ABC, ABCMeta, abstractmethod
from copy import deepcopy
from enum import Enum
from typing import Any, Dict, Mapping, Optional, Union
import warnings

import simpy

from qureed.extra import Loggers, get_custom_logger
from qureed.signals.generic_signal import GenericSignal
from qureed.simulation import Simulation
from qureed.utils import type_mapping

from .connection import Connection, resolve_connection_direction
from .exceptions import PortDirectionException
from .helpers import common_signal_type, normalize_port
from .logging_mixin import DeviceLoggingMixin
from .port import Port


class DeviceMeta(ABCMeta):
    """
    Metaclass for all devices inheriting from `GenericDevice`.

    This metaclass inspects the `port_definitions` class attribute and
    dynamically generates a `Ports` enum for convenient, type-safe port access.

    Example:
    --------
    >>>class MyDevice(GenericDevice):
    >>>    port_definitions = {
    >>>        "input": Port(...),
    >>>        "output": Port(...)
    >>>    }
    >>>
    >>> MyDevice.Ports.input  # Enum member with value "input"

    This helps improve clarity and consistency when referring to port labels.
    """

    def __new__(
        cls, name: str, bases: tuple[type, ...], dct: dict[str, Any]
    ) -> type:
        klass = super().__new__(cls, name, bases, dct)

        port_defs = getattr(klass, "port_definitions", None)
        if isinstance(port_defs, dict):
            PortsEnum = Enum("Ports", {k: k for k in port_defs})
            setattr(klass, "Ports", PortsEnum)

        return klass


class GenericDevice(DeviceLoggingMixin, ABC, metaclass=DeviceMeta):
    """
    GenericDevice defines an abstract base class for all devices in the
    QuReed framework.

    Notes:
    ------
    This class handles:
    - Port management and dynamic Enum creation
    - Property setting and validation
    - Signal transmission and delivery between devices
    - SimPy-based generator process registration

    Subclasses must define:
    - `port_definitions` (as a class attribute)
    - `gui_name` and `gui_icon` (as properties)

    Usage Example:
    --------------
    >>> from qureed.devices.generic_device import GenericDevice
    >>> from qureed.devices.port import Port
    >>> from qureed.signals.generic_signal import GenericSignal
    >>> from qureed.devices.decorators import des_proc
    >>>
    >>> class MyDevice(GenericDevice):
    ...     port_definitions = {
    ...         "in":  Port(direction="input",  signal_type=GenericSignal),
    ...         "out": Port(direction="output", signal_type=GenericSignal),
    ...     }
    ...
    ...     # This is overriden at the object creation, but usefull for
    ...     # the lsp to give the user type hints.
    ...     # <<< static hint for LSP autocomplete >>>
    ...     class Ports(Enum):
    ...         in = "in"
    ...         out = "out"
    ...     # <<< end of hint >>>
    ...
    ...     @property
    ...     def gui_name(self) -> str:
    ...         return "MyDevice"
    ...
    ...     @property
    ...     def gui_icon(self) -> str:
    ...         return "my_icon.svg"
    ...
    ...     @des_proc
    ...     def proc(self):
    ...         while True:
    ...             sig = yield self.receive("in")
    ...             yield self.sim_env.timeout(1)
    ...             self.send(self.Ports.out, sig)
    >>>
    >>> dev = MyDevice()
    >>> # Ports enum was injected:
    >>> assert MyDevice.Ports.in.value == "in"
    >>> assert MyDevice.Ports.out.value == "out"
    >>> # You can now connect dev, run the sim, etc.
    """

    # --- Class attributes and port setup ---
    reference: str | None = None
    port_definitions: Mapping[str, Port]
    Ports: type[Enum]
    properties: Dict[str, Dict[str, Any]] = {
        "name": {
            "type": str,
        }
    }

    # --- Initialization ---
    def __init__(self, uid=None, **kwargs):
        """
        Initializes the device and sets up simulation context

        Arguments:
        ----------
        uid: Optional(str)
            Optional unique identifier. Auto-generated if not provided.
        **kwargs: Any
            Additional arguments for extension/customization
        """
        self.uid = uid if uid else uuid.uuid4()
        self.properties = deepcopy(self._merge_properties())

        self.simulation = Simulation()
        self.sim_env = self.simulation.simpy_env
        self.logger = get_custom_logger(Loggers.Custom, device=self)

        self._inboxes: Dict[str, simpy.Store] = {
            port: simpy.Store(self.sim_env) for port in self.ports
        }

        self._connected_ports: Dict[str, Optional[Connection]] = {
            normalize_port(port): None for port in self.ports
        }
        self._register_processes()

    # --- Classmethod/metaclass helpers ---
    def _merge_properties(self):
        """
        Merge properties from the base class and the subclass.
        Merges default and subclass-defined properties

        Returns:
        --------
        Dict:
            A dictionary containing merged property metadata.
        """
        combined_properties = deepcopy(GenericDevice.properties)
        subclass_properties = getattr(self.__class__, "properties", {})
        combined_properties.update(subclass_properties)
        return combined_properties

    # --- Public Properties ---
    @property
    def ports(self) -> Mapping[str, Port]:
        """
        Returns:
        --------
        Dict:
            A dictionary of port definitions for this device.
        """
        return self.__class__.port_definitions

    @property
    def name(self) -> str:
        """
        Returns:
        --------
        str:
            Device name if set, UID otherwise.
        """
        return self.properties["name"].get("value", self.uid)

    @property
    @abstractmethod
    def gui_name(self) -> str:  # pragma: no cover
        """
        Returns:
        --------
        str:
            The user-facing name for the GUI

        Raises
        ------
            NotImplementedError: If not defined in the subclass
        """
        raise NotImplementedError("gui_name must be defined")

    @property
    @abstractmethod
    def gui_icon(self) -> str:  # pragma: no cover
        """
        Returns:
        --------
        str:
            Path or key to the icon used in GUI.
        """
        raise NotImplementedError("gui_icon must be defined")

    # --- Public Configuration
    def set_property(self, property_name: str, value: Any) -> None:
        """
        Sets a device property after validating and coercing the value.

        Arguments:
        ----------
        property_name: str
            The property key to update
        value: Any
            The value to assign

        Raises:
        -------
        AttributeError:
            If the property doesn't exist
        TypeError:
            If value has wrong type.
        """
        props = self.properties

        if property_name not in props:
            raise AttributeError(
                f"{self.__class__.__name__} has no property {property_name}"
            )

        prop_def = props[property_name]

        # Type Check
        allowed_types, coercer = type_mapping[prop_def["type"].__name__]

        if not isinstance(value, allowed_types):
            raise TypeError(
                f"{property_name} Expected ",
                f"{self.properties[property_name]['type']}, got {type(value)}",
            )
        self.properties[property_name]["value"] = coercer(value)

    def get_property(self, property_name: str) -> Any:
        """
        Retrieves a property value.

        Arguments:
        ----------
        property_name: str
            The property to retrieve

        Returns:
        --------
        Any:
            The stored value, or None if unset

        Raises:
        -------
        AttributeError: If the property is not defined
        """
        if property_name not in self.properties.keys():
            raise AttributeError(
                f"{self.__class__.__name__} has no property {property_name}"
            )
        return self.properties[property_name].get("value", None)

    # --- Simulation Registration
    def _register_processes(self) -> None:
        """
        Registers generator-based simulation processes.

        Processes are decorated with des_proc decorator.
        """
        found_any = False
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if inspect.ismethod(attr) and getattr(
                attr, "_is_des_process", False
            ):
                backend = getattr(attr, "_supported_backend", False)
                if backend is not None and self.simulation.backend != backend:
                    continue

                gen = attr()
                if not isinstance(gen, types.GeneratorType):
                    raise TypeError(
                        f"{self.__class__.__name__}.{gen.__name__}",
                        "is not a Generator!",
                    )
                found_any = True
                self.sim_env.process(gen)
        if not found_any:
            warnings.warn(
                f"<{self.__class__.__name__}> registered *no* @des_proc"
                f" methods for backend <{self.simulation.backend}>"
            )

    # --- Connection Logic
    def connect(
        self,
        local_port: Union[Enum, str],
        remote_device: GenericDevice,
        remote_port: Union[Enum, str],
    ) -> None:
        """
        Connects this device to another via compatible ports.

        Arguments:
        ----------
        local_port: Enum
            This device's port
        remote_device: GenericDevice
            The other device instance
        remote_port: Enum
            The other device's port

        Raises:
        -------
            PortDirectionException: If the directions are incompatible
            TypeError: If signal types cannot be reconciled.
        """
        local_port = normalize_port(local_port)
        remote_port = normalize_port(remote_port)
        local_type = self.ports[local_port].signal_type
        remote_type = remote_device.ports[remote_port].signal_type

        local_direction = self.ports[local_port].direction
        remote_direction = remote_device.ports[remote_port].direction

        if local_direction == remote_direction:
            raise PortDirectionException(
                f"Cannot connect {local_direction} to {remote_direction}"
            )
        selected_type = common_signal_type(local_type, remote_type)

        source_device, source_port, sink_device, sink_port = (
            resolve_connection_direction(
                self,
                local_port,
                local_direction,
                remote_device,
                remote_port,
                remote_direction,
            )
        )

        connection = Connection(
            source_device=source_device,
            source_port=source_port,
            sink_device=sink_device,
            sink_port=sink_port,
            signal_type=selected_type,
        )

        self._connected_ports[local_port] = connection
        remote_device._connected_ports[remote_port] = connection

    # --- Signal Routing ---
    def send(self, local_port: str | Enum, signal: GenericSignal):
        """
        Sends a signal through the specified port.

        Arguments:
        ----------
        local_port: str | Enum
            Port to send from
        signal: GenericSignal
            Signal instance to transmit

        Raises:
        -------
        `KeyError`: if port does not exist.
        `TypeError`: if Signal does not match the defined port.
        """
        signal.timestamp = self.sim_env.now
        signal.sender = self
        local_port = normalize_port(local_port)
        if local_port not in self._connected_ports.keys():
            raise KeyError(
                f"{self.__class__.__name__} does not have port: {local_port}"
            )
        expected_type = self.ports[local_port].signal_type
        if not isinstance(signal, expected_type):
            raise TypeError(
                f"Signal type mismatch on port '{local_port}': "
                f"expected {expected_type.__name__}, got",
                f"{type(signal).__name__}",
            )

        if self._connected_ports[local_port] is None:
            return

        connection = self._connected_ports[local_port]

        if connection is not None and not signal.terminate:
            target_device, remote_port = connection.get_next_device_and_port()
            target_device.deliver(remote_port, signal)

        if signal.terminate:
            signal.cleanup()

    def receive(self, local_port: str | Enum) -> Any:
        """
        Waits for a signal on the given port.

        Arguments:
        ----------
        local_port: str | Enum
            The port to listen on

        Returns:
        --------
            SimPy event representing the incoming signal.
        """
        local_port = normalize_port(local_port)
        return self._inboxes[local_port].get()

    def any_receive(self, *ports: Union[str, Enum]):
        """
        Waits for a signal to arrive on any of the specified ports.

        Arguments:
        ----------
        *ports: (str | Enum)
            One or more ports (as strings or Enum members) to listen on.

        Returns:
        --------
        list[tuple[GenericSignal, str]]:
            A list of (signal, port) tuples for signals
            received during this simulation tick.

        Raises:
        -------
            `KeyError`: If any of the ports is not valid.
        """
        normalized_ports = [normalize_port(p) for p in ports]

        for port in normalized_ports:
            if port not in self._inboxes:
                raise KeyError(
                    f"{self.__class__.__name__} has no port: {port}"
                )

        named_gets = {
            port: self._inboxes[port].get() for port in normalized_ports
        }
        event_to_port = {evt: port for port, evt in named_gets.items()}

        event = simpy.events.AnyOf(self.sim_env, list(named_gets.values()))
        result = yield event

        signals = []
        for triggered_event, signal in result.items():
            port = event_to_port[triggered_event]
            signals.append((signal, port))

        return signals

    def deliver(self, local_port: str | Enum, signal: GenericSignal) -> None:
        """
        Delivers a signal to the internal queue for the given port.

        Arguments:
        ----------
        local_port: str | Enum
            Target port.
        signal: GenericSignal
            Signal instance to enqueue
        """
        local_port = normalize_port(local_port)
        self._inboxes[local_port].put(signal)

    # --- Dunder methods
    def __repr__(self):
        return f"<{self.__class__.__name__} name={self.name} uid={self.uid}>"
