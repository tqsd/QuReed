from .generic_clock_device import GenericClockDevice
from qureed.devices import des_proc
from qureed.signals import TriggerSignal

class ConstantClock(GenericClockDevice):
    """
    Emits periodic `TriggerSignal`s at a constant rate defined by the `frequency` property.

    This clock device starts ticking at `start_time` (if current time is earlier)
    and continues to emit signals until the simulation time reaches `end_time`.
    The interval between ticks is computed as the inverse of `frequency`.

    Properties:
    -----------
    frequency : float
        The number of tick signals emitted per unit of simulation time.
        For example, `frequency = 1.0` means one tick per second.
        Inherited from `GenericClockDevice`.


    Ports:
    ------
    tick : output
        Emits a `TriggerSignal` every `1/frequency` time units, starting
        from `start_time` up to `end_time`.

    GUI Metadata:
    -------------
    gui_name : str
        "Constant Clock" — used for labeling this device in the graphical UI.

    Example:
    --------
    >>> clock = ConstantClock()
    >>> clock.set_property("frequency", 2.0)      # 2 Hz = tick every 0.5s
    >>> # At simulation time 0.0, it begins ticking: 0.0, 0.5, 1.0, ...

    Notes:
    ------
    - The `TriggerSignal` does not carry a payload; its presence is the event.
    - The `send()` method automatically sets `timestamp` and `sender`.
    - If `frequency <= 0`, no ticks will be emitted (can be validated externally).
    """

    @property
    def gui_name(self) -> str:
        return "Constant Clock"

    @des_proc
    def proc(self):
        """
        Main simulation process for ticking behavior.

        This coroutine runs in the SimPy event loop. It emits a `TriggerSignal`
        at the beginning of the simulation and then waits for `1/frequency` time
        units before the next click.
        
        This method is automatically registered via `@des_proc` so it runs
        as part of the simulation.
        """
        frequency = self.get_property("frequency")
        while True:
            self.send(self.Ports.tick, TriggerSignal())
            yield self.sim_env.timeout(1/self.get_property("frequency"))
