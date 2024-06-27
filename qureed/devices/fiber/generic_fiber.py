"""
This module implements a generic fiber
all fibers must extend this fiber abstraction
"""

from abc import ABC, ABCMeta

from qureed.devices import Port
from qureed.devices.generic_device import GenericDevice
from qureed.signals.generic_float_signal import GenericFloatSignal
from qureed.signals.generic_quantum_signal import GenericQuantumSignal


class EnforcePortsMeta(ABCMeta):
    def __init__(cls, name, bases, namespace, **kwargs):
        super().__init__(name, bases, namespace)
        # Only enforce ports structure on subclasses, not on GenericDevice itself
        if bases != (ABC,) and "GenericDevice" in [base.__name__ for base in bases]:
            # Ensure the class has a 'ports' class variable and it's a dictionary
            if not hasattr(cls, "ports") or not isinstance(cls.ports, dict):
                raise TypeError(
                    f"{cls.__name__} must have a 'ports' class variable of type dict"
                )

            # Specify the required keys
            required_keys = {"length", "input", "output"}
            # Check if the 'ports' dictionary has all the required keys
            if not required_keys.issubset(cls.ports.keys()):
                missing_keys = required_keys - cls.ports.keys()
                raise TypeError(
                    f"{cls.__name__}'s 'ports' dictionary is missing keys: {missing_keys}"
                )


class GenericFiber(GenericDevice, metaclass=EnforcePortsMeta):
    """
    Generic Fiber specifies the format for all Fiber Devices
    Every Fiber device must extend this abstract base class
    """

    ports = {
        "length": Port(
            label="control",
            direction="length",
            signal=None,
            signal_type=GenericFloatSignal,
            device=None,
        ),
        "input": Port(
            label="input",
            direction="input",
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None,
        ),
        "output": Port(
            label="output",
            direction="output",
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None,
        ),
    }

    def set_length(self, length: float):
        """
        Sets the length of the fiber
        """
        length_signal = GenericFloatSignal()
        length_signal.set_float(length)
        self.register_signal(signal=length_signal, port_label="length")
        length_signal.set_computed()
