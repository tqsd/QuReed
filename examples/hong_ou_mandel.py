"""
Example: Hong-Ou-Mandel Experiment
"""

from qureed.simulation import Simulation
from qureed.experiement import Experiement
from qureed.components.gates import Squeezing, Beamsplitter
from math import pi

Sim = Simulation.get_instance()

squeezing_gate = Squeezing(r=2, phi=0)

bs_gate = Beamsplitter(theta=0.5, phi=pi / 2)


exp_1 = Experiement()

exp_1.state_init("type of state")
exp_1.add_operation(squeezing_gate, modes=0)
exp_1.add_operation(bs_gate, modes=[0, 1])

Sim.execute(exp_1)
