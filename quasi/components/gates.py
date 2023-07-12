from abc import ABC
from quasi._math.fock import displacment, beamsplitter, phase, squeezing


class Components(ABC):
    """
     singlton

    we should agree on specific methods and properties that relates to
    signals.
    """

    def get_operator(self):
        raise NotImplementedError


class Beamsplitter(Components):
    def __init__(self, theta, phi, cutoff) -> None:
        self.theta = theta
        self.phi = phi
        self.cutoff = cutoff
        super().__init__()

    def get_operator(self):
        return beamsplitter(self.theta, self.phi, self.cutoff)


class Displacment(Components):
    def __init__(self, r, phi, cutoff) -> None:
        self.theta = r
        self.phi = phi
        self.cutoff = cutoff
        super().__init__()

    def get_operator(self):
        return displacment(self.r, self.phi, self.cutoff)


class Squeezing(Components):
    def __init__(self, r, phi, cutoff) -> None:
        self.theta = r
        self.phi = phi
        self.cutoff = cutoff
        super().__init__()

    def get_operator(self):
        return squeezing(self.r, self.phi, self.cutoff)


class Phase(Components):
    def __init__(self, phi, cutoff) -> None:
        self.phi = phi
        self.cutoff = cutoff
        super().__init__()

    def get_operator(self):
        return phase()(self.phi, self.cutoff)
