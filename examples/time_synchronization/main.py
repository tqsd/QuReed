# General libraries
import os
import sys
import mpmath

# qureed elements
from qureed.simulation import Simulation
from qureed.devices.control import SimpleTrigger
from qureed.signals import GenericBoolSignal, GenericQuantumSignal

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from time_synchronization.custom_components.entangled_photon_source import (
    EntangledPhotonSource,
)
from time_synchronization.custom_components.custom_fiber import CustomFiber
from time_synchronization.custom_components.custom_filter import CustomFilter


# Helper function for connecting
def connect(signal_type, device, port, device2=None, port2=None):
    signal = signal_type()
    device.register_signal(signal, port)
    if device2 is not None and port2 is not None:
        device2.register_signal(signal, port2)
    return signal


signals = {}

# Devices
st = SimpleTrigger(time=mpmath.mpf("0.0000000000001"), name="Trigger")
source = EntangledPhotonSource(name="Source")
fiber1 = CustomFiber("Fiber1", 1)
fltr = CustomFilter("Filter")


# Connecting the devices
signals["1"] = connect(GenericBoolSignal, st, "trigger", source, "trigger")
signals["2"] = connect(GenericQuantumSignal, source, "output", fiber1, "input")
signals["3"] = connect(GenericQuantumSignal, fiber1, "output", fltr, "input")


# Running the Simulation
simulation = Simulation.get_instance()
simulation.run_des(1)
