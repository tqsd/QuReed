"""
Ideal Beam Splitter experiment example
"""

from qureed.simulation import Simulation, SimulationType
from qureed.devices.sources import IdealNPhotonSource, IdealCoherentSource
from qureed.devices.control import SimpleTrigger
from qureed.devices.beam_splitters import IdealBeamSplitter
from qureed.signals import GenericBoolSignal, GenericQuantumSignal
from qureed.experiment import Experiment
from qureed.backend.fock_first_backend import FockBackendFirst
import numpy as np

np.set_printoptions(precision=3, suppress=True)

sim = Simulation()
sim.set_backend(FockBackendFirst())
sim.set_dimensions(5)

sim.set_simulation_type(SimulationType.FOCK)

s1 = IdealCoherentSource()
s1.set_displacement(2, 0)
# s1 = IdealNPhotonSource()
# s1.set_photon_num(1)


s2 = IdealNPhotonSource()
s2.set_photon_num(0)

st1 = SimpleTrigger()
sig_trigger_1 = GenericBoolSignal()
st1.register_signal(signal=sig_trigger_1, port_label="trigger")

st2 = SimpleTrigger()
sig_trigger_2 = GenericBoolSignal()
st2.register_signal(signal=sig_trigger_2, port_label="trigger")


bs = IdealBeamSplitter()

qs1 = GenericQuantumSignal()
s1.register_signal(signal=qs1, port_label="output")
bs.register_signal(signal=qs1, port_label="A")
qs2 = GenericQuantumSignal()
s2.register_signal(signal=qs2, port_label="output")
bs.register_signal(signal=qs2, port_label="B")


sim.run()

exp = Experiment.get_instance()

print(exp.state.all_fock_probs())
state = exp.state
print(state.mean_photon(mode=[0]))
print(state.mean_photon(mode=[1]))
