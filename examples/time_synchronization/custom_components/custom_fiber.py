"""

 created with template
"""
from typing import Union
from quasi.devices import (GenericDevice,
                           wait_input_compute,
                           schedule_next_event,
                           coordinate_gui,
                           log_action,
                           ensure_output_compute)

from quasi.devices.port import Port
from quasi.simulation import ModeManager
from quasi.simulation.constants import C
from quasi.signals import *


class CustomFiber(GenericDevice):
    ports = {
        
        "input": Port(
            label="input",
            direction="input",
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None),
        
        
        "output": Port(
            label="output",
            direction="output",  # Changed from "input" to "output" for clarity
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None),
        
    }
    
    gui_icon = None
    gui_tags = None
    gui_documentation= None
    
    power_peak = 0
    power_average = 0
    
    reference = None

    def __init__(self, name, uid, length=-1):
        super().__init__(name, uid)
        self.length=length

    def set_length(self, length):
        self.length = length
      
    @ensure_output_compute
    @coordinate_gui
    @wait_input_compute
    def compute_outputs(self, *args, **kwargs):
    	"""
	Implement to use the regular backend
	"""
    	pass
      
    @log_action
    @schedule_next_event
    def des(self, time, *args, **kwargs):
        """
	Implement to use discrete event simulation
	"""
        n = 1.45
        # Speed of light in fiber
        v = C/n
        t = self.length/v
        s = kwargs["signals"]["input"]
        env = s.contents

        return [("output", s, time+t)]

    @log_action
    @schedule_next_event
    def des_action(self, time=None, *args, **kwargs):
        """
	Or implement this if you are implementing a trigger
	"""
        pass
