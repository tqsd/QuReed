from qureed.simulation import Simulation
from qureed.devices.control import ClockTrigger
from qureed.devices.variables import FloatVariable
from qureed.devices.sources import IdealCoherentSource
from qureed.signals import GenericBoolSignal, GenericFloatSignal


# Helper function for connecting
def connect(signal_type, device, port, device2=None, port2=None):
    signal = signal_type()
    device.register_signal(signal, port)
    if device2 is not None and port2 is not None:
        device2.register_signal(signal, port2)
    return signal


signals = {}


main_trigger = ClockTrigger("Clock")
frequency_variable = FloatVariable("Frequency")
frequency_variable.set_value(10)  # 10 Herz
alpha_variable = FloatVariable("Alpha")
alpha_variable.set_value(1)
phi_variable = FloatVariable("Phi")
phi_variable.set_value(0)
source = IdealCoherentSource("Source")
signals["clock_frequency"] = connect(
    GenericFloatSignal, frequency_variable, "float", main_trigger, "frequency"
)
signals["alpha"] = connect(GenericFloatSignal, alpha_variable, "float", source, "alpha")
signals["phi"] = connect(GenericFloatSignal, phi_variable, "float", source, "phi")
signals["trigger_source"] = connect(
    GenericBoolSignal, main_trigger, "trigger", source, "trigger"
)


simulation = Simulation.get_instance()
simulation.run_des(0.5)
