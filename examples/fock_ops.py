from quasi.components.gates import Beamsplitter, Displacment, Phase, Squeezing
from quasi._math.fock import vacuum_state, mean_photon_number, fock_probability
from quasi.components.gates import Components
import numpy as np

qumode = 1
cutoff = 10
init_state = vacuum_state(n=qumode, cutoff=cutoff)

user_defined_component = Components(cutoff=cutoff)
user_defined_component.matrix = np.identity(n=10)

displacement_operator = Displacment(1, 0.5, cutoff=10).matrix

displaced_state = displacement_operator @ init_state

displaced_state_unphased = Phase(-0.5, cutoff=10).matrix @ displaced_state

assert mean_photon_number(state=displaced_state) == 1**2

assert fock_probability([0], displaced_state) == displaced_state[0].real ** 2
