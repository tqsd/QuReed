

from qureed.devices.generic_device import (
    GenericDevice,
    log_action,
    schedule_next_event,
    )
from qureed.devices.port import Port
from qureed.signals import (
    GenericSignal,
    GenericQuantumSignal
    )

class Anchor(GenericDevice):

    ports = {
        "in": Port(
            label="in",
            direction="input",
            signal=None,
            signal_type=GenericSignal,
            device=None,
            ),
        "out": Port(
            label="out",
            direction="output",
            signal=None,
            signal_type=GenericSignal,
            device=None,
        )
        }
    
    gui_icon = None
    gui_tags = ["anchor", "label", "gui"]
    gui_name = "Anchor"
    gui_documentation = None
    reference = None


    @schedule_next_event
    @log_action
    def des(self, time, *args, **kwargs):
        if "in" in kwargs.get("signals"):
            signal = kwargs["signals"]["in"]
            result = [("out", signal, time)]
            return result

    
