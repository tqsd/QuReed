"""
Variable
"""
from enum import StrEnum
from qureed.devices import (
    GenericDevice,
    coordinate_gui,
    log_action,
    schedule_next_event,
)
from qureed.devices.port import Port
from qureed.assets import icon_list
from qureed.signals import (
    GenericSignal,
    GenericBoolSignal,
    GenericIntSignal,
    GenericComplexSignal,
    GenericFloatSignal,
    GenericStringSignal,
    )
from qureed.simulation import Simulation

class VariableTypes(StrEnum):
    FLOAT="float"
    CMPLX="cmplx"
    INT="int"
    BOOL="bool"
    STR="str"
    ENUM="enum"


class Variable(GenericDevice):
    """
    Implements integer variable setter
    """

    ports = {
        "value": Port(
            label="value",
            direction="output",
            signal=None,
            signal_type=GenericSignal,
            device=None,
        ),
    }

    # Gui Configuration
    gui_icon = icon_list.SIMPLE_TRIGGER
    gui_tags = ["variable"]
    gui_name = "Variable"
    power = 0
    power_average = 0
    power_peak = 0
    reference = None

  
    properties = {
        "variable_type":{
            "type": VariableTypes,
             },
        "value":{
            "type": object,
             }
        }

    def __init__(self, time=-1, uid=None):
        super().__init__(uid=uid)
        self.time = time
        self.simulation = Simulation.get_instance()
        self.simulation.schedule_event(time, self)

    def set_variable_type(self, variable_type:VariableTypes):
        signal_type = GenericSignal
        match variable_type:
            case VariableTypes.FLOAT:
                signal_type = GenericFloatSignal
                variable_type = float
            case VariableTypes.INT:
                signal_type = GenericIntSignal
                variable_type = int
            case variable_type.BOOL:
                signal_type = GenericBoolSignal
                variable_type = bool
            case variable_type.STR:
                signal_type = GenericStringSignal
                variable_type = str
            case variable_type.CMPLX:
                signal_type = GenericComplexSignal
                variable_type = complex
            case _:
                variable_type = object
        self.properties["value"]["type"] = variable_type
        self.properties["value"]["value"] = None
        self.ports["value"].signal_type = signal_type
        
    def set_value(self, value: str):
        self.properties["value"]["value"] = int(value)

    @log_action
    @schedule_next_event
    def des(self, time, *args, **kwargs):
        signal = GenericIntSignal()
        signal.set_int(int(self.values["value"]))
        result = [("int", signal, time + 0)]
        return result

    @log_action
    @schedule_next_event
    def des_action(self, time=None, *args, **kwargs):
        next_device, port = self.get_next_device_and_port("int")
        signal = GenericIntSignal()
        signal.set_int(int(self.values["value"]))
        result = [("int", signal, self.time)]
        return result
