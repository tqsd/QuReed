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
    GenericIntSignal,
    GenericBoolSignal,
    GenericQuantumSignal,
    GenericTimeSignal,
)

from quasi.gui.icons import icon_list


class ClockTrigger(GenericDevice):
    """
    Implements Simple Trigger,
    Trigger turns on at the start of simulation.
    """

    ports = {
        "pulse_num": Port(
            label="pulse_num",
            direction="input",
            signal=None,
            signal_type=GenericIntSignal,
            device=None,
        ),
        "delay": Port(
            label="delay",
            direction="input",
            signal=None,
            signal_type=GenericTimeSignal,
            device=None,
        ),
        "frequency": Port(
            label="frequency",
            direction="input",
            signal=None,
            signal_type=GenericFloatSignal,
            device=None,
        ),
        "trigger": Port(
            label="trigger",
            direction="output",
            signal=None,
            signal_type=GenericBoolSignal,
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
        self._triger_count = 0
        self.frequency = frequency
        self.time = time
        self.pulse_num = -1
        self.delay = 0
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
        signals = kwargs.get("signals")
        if "frequency" in signals:
            self.frequency = signals["frequency"].contents
        if "pulse_num" in signals:
            self.pulse_num = signals["pulse_num"].contents
            if not self.pulse_num == 0:
                self.pulse_num -= 1
        if "delay" in signals:
            self.delay = signals["delay"].contents
            self.simulation.schedule_event(self.delay, self)
        if self._should_trigger(time):
            if self.frequency is None:
                raise Exception("Frequency not set")
            else:
                if not self.pulse_num == 0:
                    self.simulation.schedule_event(time + 1 / self.frequency, self)
                    self.pulse_num -= 1
                signal = GenericBoolSignal()
                signal.set_bool(True)
                self._triger_count += 1
                result = [("trigger", signal, time)]
                return result

    def _should_trigger(self, time) -> bool:
        if self.frequency is None:
            return False

        if time < self.delay:
            return False

        # Define a tolerance value to account for floating-point inaccuracies
        tolerance = 1e-9

        # Calculate the difference and the modulus
        diff = time - self.delay
        mod_result = diff % (1 / self.frequency)

        # Check if the modulus result is close to zero within the tolerance
        if (
            abs(mod_result) < tolerance
            or abs(mod_result - (1 / self.frequency)) < tolerance
        ):
            return True
        return False
