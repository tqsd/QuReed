
from quasi.simulation import Simulation
from quasi.devices.control import SimpleTrigger
from quasi.devices.sources import IdealNPhotonSource
from quasi.signals import GenericBoolSignal
import mpmath

st = SimpleTrigger(time=mpmath.mpf('0'), name="ST")
source = IdealNPhotonSource(name="Source")
source.set_photon_num(5)
sig = GenericBoolSignal()
st.register_signal(signal=sig, port_label="T")
source.register_signal(signal=sig, port_label="trigger")


simulation = Simulation.get_instance()

simulation.run_des(mpmath.mpf('1'))
