from quasi.simulation import Simulation
from quasi.experiement import Experiement
from quasi.components.gates import Squeezing, Beamsplitter, Phase
from math import pi
import numpy as np
from quasi._math.fock import mean_photon
from quasi._math.fock.ops import fock_state, tensor, vacuumStateMixed, adagger, apply_gate_BLAS, fock_operator


squeezing_gate = Squeezing(r=0.1, phi=pi, cutoff=3)

bs_gate = Beamsplitter(theta=pi/4, phi=pi/2, cutoff=3)

phase_gate = Phase(phi=pi/4, cutoff=10)

exp_1 = Experiement(num_modes=3, cutoff=3)

exp_1.state_init(1, modes=[0])

#exp_1.add_operation(bs_gate.get_operator().transpose((0, 2, 1, 3)), [0, 1])
#exp_1.add_operation(squeezing_gate.get_operator(), [0])

exp_1.execute()

state = exp_1.state
print(state.dm().shape)

