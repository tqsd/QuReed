"""
Int Variable
"""
import inspect
import traceback
from qureed.devices import (
    GenericDevice,
    coordinate_gui,
    log_action,
    schedule_next_event,
)
from qureed.devices.port import Port
from qureed.assets import icon_list
from qureed.signals import GenericIntSignal
from qureed.simulation import Simulation

def trace_caller():
    frame = inspect.currentframe().f_back  # Get caller's frame
    caller = inspect.getframeinfo(frame)
    
    print(f"🔹 Called from: {caller.filename}:{caller.lineno}")
    print(f"🔹 Function: {caller.function}")

class IntVariable(GenericDevice):
    """
    Implements integer variable setter
    """

    ports = {
        "int": Port(
            label="int",
            direction="output",
            signal=None,
            signal_type=GenericIntSignal,
            device=None,
        ),
    }

    # Gui Configuration
    gui_icon = icon_list.SIMPLE_TRIGGER
    gui_tags = ["variable", "integer"]
    gui_name = "Int Variable"
    power = 0
    power_average = 0
    power_peak = 0
    reference = None

    def __init__(self, name=None, time=-1, uid=None, trigger=True):
        super().__init__(name=name, uid=uid)
        self.time = time
        if trigger:
            self.simulation = Simulation.get_instance()
            self.simulation.schedule_event(time, self)

    properties = {
        "value": {
            "type": int
            }
        }

    @log_action
    @schedule_next_event
    def des(self, time, *args, **kwargs):
        signal = GenericIntSignal()
        signal.set_int(int(self.properties["value"]["value"]))
        result = [("int", signal, time + 0)]
        return result

    @log_action
    @schedule_next_event
    def des_action(self, time=None, *args, **kwargs):
        next_device, port = self.get_next_device_and_port("int")
        signal = GenericIntSignal()
        signal.set_int(int(self.properties["value"]["value"]))
        result = [("int", signal, self.time)]
        return result
