"""
Ideal Beam Splitter experiment example
"""

from quasi.simulation import Simulation, SimulationType
from quasi.devices.sources import IdealNPhotonSource
from quasi.devices.control import SimpleTrigger
from quasi.signals import GenericBoolSignal
from quasi.experiment import Experiment

sim = Simulation()
sim.set_simulation_type(SimulationType.FOCK)


s1 = IdealNPhotonSource()
s1.set_photon_num(2)

st = SimpleTrigger()
sig_trigger = GenericBoolSignal()
st.register_signal(signal=sig_trigger, port_label="trigger")

sim.run()

exp = Experiment.get_instance()
print(exp.state.all_fock_probs())
