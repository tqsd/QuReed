"""
Ideal Beam Splitter experiment example
"""

from quasi.simulation import Simulation, SimulationType
from quasi.devices.sources import IdealNPhotonSource
from quasi.devices.control import SimpleTrigger
from quasi.signals import GenericBoolSignal
from quasi.experiment import Experiment
from quasi.backend.fock_first_backend import FockBackendFirst

sim = Simulation()
sim.set_backend(FockBackendFirst())
sim.set_dimensions(3)

sim.set_simulation_type(SimulationType.FOCK)


s1 = IdealNPhotonSource()
s1.set_photon_num(1)

st = SimpleTrigger()
sig_trigger = GenericBoolSignal()
st.register_signal(signal=sig_trigger, port_label="trigger")

sim.run()

exp = Experiment.get_instance()
print(exp.state.all_fock_probs())
print(exp.num_modes)
