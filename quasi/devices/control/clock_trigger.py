"""
Clock Trigger
"""

from quasi.devices import (
    GenericDevice,
    wait_input_compute,
    coordinate_gui,
    ensure_output_compute,
    log_action,
    schedule_next_event,
)
from quasi.devices.port import Port
from quasi.simulation import Simulation
from quasi.signals import (
    GenericSignal,
    GenericFloatSignal,
    GenericBoolSignal,
    GenericQuantumSignal,
)

from quasi.gui.icons import icon_list


class ClockTrigger(GenericDevice):
    """
    Implements Simple Trigger,
    Trigger turns on at the start of simulation.
    """

    ports = {
        "trigger": Port(
            label="trigger",
            direction="output",
            signal=None,
            signal_type=GenericBoolSignal,
            device=None,
        ),
        "frequency": Port(
            label="frequency",
            direction="input",
            signal=None,
            signal_type=GenericFloatSignal,
            device=None,
        ),
    }

    # Gui Configuration
    gui_icon = icon_list.CLOCK_TRIGGER
    gui_tags = ["control"]
    gui_name = "Clock Trigger"
    power = 0
    power_average = 0
    power_peak = 0
    reference = None

    def __init__(self, name=None, frequency=None, time=0, uid=None):
        super().__init__(name=name, uid=uid)
        self.frequency = frequency
        self.time = time
        self.simulation = Simulation.get_instance()
        self.simulation.schedule_event(time, self)

    @ensure_output_compute
    @coordinate_gui
    @wait_input_compute
    def compute_outputs(self, *args, **kwargs):
        """
        Reimplement this,
        This component is a currently implemented as a visual
        demo only.
        """
        self.ports["trigger"].signal.set_bool(True)
        self.ports["trigger"].signal.set_computed()

    @log_action
    @schedule_next_event
    def des_action(self, time=None, *args, **kwargs):
        if self.frequency is not None:
            dt = 1 / self.frequency
            signal = GenericBoolSignal()
            signal.set_bool(True)
            result = [("trigger", signal, time + dt)]
            return result
        return []

    @coordinate_gui
    @schedule_next_event
    @log_action
    def des(self, time, *args, **kwargs):
        if self.frequency is None:
            self.frequency = self._extract_frequency(kwargs)
            if self.frequency is not None:
                self.simulation.schedule_event(time + 1 / self.frequency, self)
            return

        signal = self._create_and_set_signal()
        result = [("trigger", signal, time)]

        dt = 1 / self.frequency
        self.simulation.schedule_event(time + dt, self)
        return result

    def _extract_frequency(self, kwargs):
        signals = kwargs.get("signals")
        if signals and "frequency" in signals:
            return signals["frequency"].contents

    def _create_and_set_signal(self):
        """
        Creates a generic boolean signal and sets its value to True
        """
        signal = GenericBoolSignal()
        signal.set_bool(True)
        return signal
