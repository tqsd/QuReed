from .custom_phase_shifter_device import CustomPhaseShift


from qureed.simulation import Simulation, SimulationType, ModeManager
from qureed.devices.sources import IdealNPhotonSource, IdealCoherentSource
from qureed.devices.control import SimpleTrigger
from qureed.backend.fock_first_backend import FockBackendFirst
from qureed.signals import GenericBoolSignal, GenericQuantumSignal

import numpy as np
from math import pi

np.set_printoptions(suppress=True)
np.set_printoptions(linewidth=200)

sim = Simulation()
sim.set_backend(FockBackendFirst())
sim.set_dimensions(3)


S = IdealNPhotonSource("Source")
S.set_photon_num(1)
trigger = SimpleTrigger()

signals = {}
signals["trigger"] = GenericBoolSignal()
signals["qsig1"] = GenericQuantumSignal()

trigger.register_signal(signal=signals["trigger"], port_label="trigger")
S.register_signal(signal=signals["trigger"], port_label="trigger")

PS = CustomPhaseShift("Custom Phase Shift")
PS.set_params(pi / 4, 1, 1, 0)

S.register_signal(signal=signals["qsig1"], port_label="output")
PS.register_signal(signal=signals["qsig1"], port_label="input")

state = exp.state
print(state.all_fock_probs())
