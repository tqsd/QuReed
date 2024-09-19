from qureed.simulation import Simulation
from qureed.devices.control import SimpleTrigger
from qureed.devices.sources import IdealNPhotonSource
from qureed.devices.fiber import IdealFiber
from qureed.devices.detectors import IdealDetector
from qureed.signals import GenericBoolSignal, GenericQuantumSignal
import mpmath

st = SimpleTrigger(time=mpmath.mpf("0"), name="ST")
source = IdealNPhotonSource(name="Source")
source.set_photon_num(5)
sig = GenericBoolSignal()
st.register_signal(signal=sig, port_label="trigger")
source.register_signal(signal=sig, port_label="trigger")
fiber = IdealFiber("F1")
fiber.set_length(4)
qsig1 = GenericQuantumSignal()
source.register_signal(signal=qsig1, port_label="output")
fiber.register_signal(signal=qsig1, port_label="input")
detector = IdealDetector("Detector")
qsig2 = GenericQuantumSignal()
fiber.register_signal(signal=qsig2, port_label="output")
detector.register_signal(signal=qsig2, port_label="input")


simulation = Simulation.get_instance()
simulation.run_des(mpmath.mpf("1"))
