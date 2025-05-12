from abc import ABC
from enum import Enum
from typing import Dict, Any

from qureed.devices.generic_device import GenericDevice
from qureed.devices.port import Port
from qureed.signals import TriggerSignal
from qureed.assets import icon_list


class GenericOpticalSourceDevice(GenericDevice, ABC):

    properties: Dict[str, Dict[str, Any]] = {}

    # <<< static hint for LSP autocomplete >>>
    class Ports(Enum):
        trigger = "trigger"

    # <<< end of type hint >>>

    port_definitions = {
        "trigger": Port(direction="input", signal_type=TriggerSignal)
    }

    @property
    def gui_icon(self) -> str:
        return icon_list.N_PHOTON_SOURCE
