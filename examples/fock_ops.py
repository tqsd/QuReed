from qureed.components.gates import Beamsplitter, Displacment, Phase, Squeezing
from qureed._math.fock import (
    vacuum_state,
    mean_photon_number,
    fock_probability,
)
from qureed.components.gates import Components
import numpy as np

qumode = 1
cutoff = 10
init_state = vacuum_state(n=qumode, cutoff=cutoff)

doi = "https://doi.org/10.1088/1742-6596/1612/1/012015"
user_defined_component = Components(cutoff=cutoff, doi=doi)

user_defined_component.matrix = np.identity(n=10)
bibtex_file = user_defined_component.generate_bibtex(doi)

displacement_operator = Displacment(1, 0.5, cutoff=10).matrix

displaced_state = displacement_operator @ init_state

displaced_state_unphased = Phase(-0.5, cutoff=10).matrix @ displaced_state

assert mean_photon_number(state=displaced_state) == 1**2

assert fock_probability([0], displaced_state) == displaced_state[0].real ** 2
