"""
Float Variable
"""

from qureed.devices import (
    GenericDevice,
    coordinate_gui,
    log_action,
    schedule_next_event,
)
from qureed.extra.logging import Loggers, get_custom_logger
from qureed.devices.port import Port
from qureed.assets import icon_list
from qureed.signals import GenericTimeSignal

logger = get_custom_logger(Loggers.Devices)

class TimeVariable(GenericDevice):
    """
    Implements integer variable setter
    """

    ports = {
        "time": Port(
            label="time",
            direction="output",
            signal=None,
            signal_type=GenericTimeSignal,
            device=None,
        ),
    }

    # Gui Configuration
    gui_icon = icon_list.SIMPLE_TRIGGER
    gui_tags = ["variable", "time"]
    gui_name = "Time Variable"
    power = 0
    power_average = 0
    power_peak = 0
    reference = None

    properties = {
        "value": {
            "type": float
            }
        }

    def set_value(self, value: str):
        self.properties["value"]["value"] = float(value)

    def __init__(self, name=None, uid=None, trigger=True):
        super().__init__(name=name, uid=uid)
        if trigger:
            self.simulation.schedule_event(-1, self)

    @log_action
    @schedule_next_event
    def des_action(self, time=None, *args, **kwargs):
        logger.info("HERE")
        signal = GenericTimeSignal()
        logger.info("SIGNAL")
        signal.set_time(self.properties["value"]["value"])
        result = [("time", signal, time)]
        return result
