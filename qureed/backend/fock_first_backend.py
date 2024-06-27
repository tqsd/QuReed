"""
This module integrated first fock backend into the qureed backend
"""
import cmath

from qureed._math.fock import a, adagger, beamsplitter, displacement, phase, squeezing
from qureed.backend.backend import FockBackend
from qureed.experiment import Experiment


class FockBackendFirst(FockBackend):
    """
    First Fock Backend integration
    """

    def __init__(self):
        self.experiment = Experiment()
        self.number_of_modes = 0

    def initialize(self):
        """
        Initialization method is run befor the simulation
        """
        # self.experiment.prepare_experiment()

    def set_number_of_modes(self, number_of_modes):
        """
        Set the number of modes
        """
        print(f"Number of modes {number_of_modes}")
        self.number_of_modes = number_of_modes
        self.experiment.update_mode_number(num_modes=number_of_modes)

    def set_dimensions(self, dimensions):
        """
        Set the number of modes
        """
        print(f"Dimensions {dimensions}")
        self.experiment.update_dimensions(dimensions)

    def create(self, mode):
        """
        Return the creation operator
        """
        return adagger(self.experiment.cutoff)

    def destroy(self, mode):
        """
        Return the annihilatio operator
        """
        return a(self.experiment.cutoff)

    def squeeze(self, z: complex, mode):
        """
        Return the squeezing operator
        """
        return squeezing(abs(z), cmath.phase(z), self.experiment.cutoff)

    def displace(self, alpha: float, phi: float, mode):
        """
        Returns the displace operator
        """
        return displacement(alpha, phi, self.experiment.cutoff)

    def phase_shift(self, theta: float, mode):
        return phase(theta, self.experiment.cutoff)

    def number(self, mode):
        pass

    def apply_operator(self, operator, modes):
        print(f"apply_operator: {modes}")
        print([*modes])
        self.experiment.add_operation(operator, modes)

    def initialize_number_state(self, n: int, mode: int):
        """
        Initialize the number state
        """
        self.experiment.state_init(n, mode)

    def beam_splitter(self, theta=0, phi=0):
        """
        Returns the beamsplitter operator
        """
        return beamsplitter(theta, phi, self.experiment.cutoff).transpose((0, 2, 1, 3))
