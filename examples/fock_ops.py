from quasi.components.gates import Beamsplitter, Displacment, Phase, Squeezing
from quasi._math.fock import vacuum_state, mean_photon_number, fock_probability


qumode = 1
cutoff = 10
init_state = vacuum_state(n=qumode, cutoff=cutoff)

displacement_operator = Displacment(1, 0.5, cutoff=10)

displaced_state = displacement_operator @ init_state

assert mean_photon_number(state=displaced_state) == 1**2

assert fock_probability([0], displaced_state) == displaced_state[0].real ** 2
