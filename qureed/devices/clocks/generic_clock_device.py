from abc import ABC, abstractmethod
from typing import Dict, Any

from qureed.devices.generic_device import GenericDevice
from qureed.devices.port import Port
from qureed.signals import TriggerSignal
from qureed.assets import icon_list

class GenericClockDevice(GenericDevice, ABC):
    """
    Abstract base class for all clock-like devices in the QuReed simulation framework.

    Clock devices are responsible for emitting periodic or event-based `TriggerSignal`s
    on their output port named `"tick"`. These signals are typically used to activate
    or synchronize other components in the simulation (e.g., triggering detectors,
    launching pulses, or synchronizing computation steps).

    This base class defines:
    - A common `"tick"` output port that emits `TriggerSignal`s
    - Standard time-related properties (`frequency`, `start_time`, `end_time`)
    - A required abstract `proc()` method that subclasses must implement to define
      the ticking behavior using the SimPy event loop

    Subclass Responsibilities:
    --------------------------
    Subclasses must implement the `proc()` method decorated with `@des_proc`, and
    override the `gui_name` property to provide a user-facing label for the device.

    Properties:
    -----------
    frequency : float
        Number of ticks per unit of simulation time.
    start_time : float
        Simulation time at which ticking should begin.
    end_time : float
        Simulation time after which no further ticks should be emitted.

    Ports:
    ------
    tick : output
        Emits a `TriggerSignal` on each tick event.

    GUI Metadata:
    -------------
    gui_icon : str
        Returns a symbolic constant representing the icon for clock devices.
        Subclasses must define `gui_name` for GUI display.

    Example:
    --------
    >>> class ConstantClock(GenericClockDevice):
    ...     @property
    ...     def gui_name(self) -> str:
    ...         return "Constant Clock"
    ...
    ...     @des_proc
    ...     def proc(self):
    ...         while self.sim_env.now < self.get_property("end_time"):
    ...             yield self.sim_env.timeout(1 / self.get_property("frequency"))
    ...             self.send(self.Ports.tick, TriggerSignal(sender=self))

    """

    properties: Dict[str, Dict[str, Any]] = {
        "frequency": {
            "type": float
            },
        }
    
    port_definitions = {
        "tick": Port(direction="output", signal_type=TriggerSignal)
    }

    @property
    def gui_icon(self) -> str:
        return icon_list.CLOCK_TRIGGER

    @abstractmethod
    def proc(self):
        """
        Simulation process that emits a clock tick signal.

        Subclasses must implement this method to define how and when
        tick signals are emitted. The method must be decorated with
        `@des_proc` so it gets registered as a SimPy process during simulation.

        This method typically uses `self.sim_env.timeout(...)` to schedule
        ticks, and emits `TriggerSignal`s using `self.send(...)`.
        """
        pass

    
