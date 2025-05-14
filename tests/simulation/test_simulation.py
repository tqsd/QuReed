import unittest

from qureed.backends.exceptions import UnknownBackendException
from qureed.simulation import Simulation


class TestSimulationClass(unittest.TestCase):
    def setUp(self) -> None:
        Simulation.reset()

    def tearDown(self) -> None:
        Simulation.reset()

    def test_raises_unknown_backend(self):
        with self.assertRaises(UnknownBackendException):
            sim = Simulation(backend="fake_backend")
        with self.assertRaises(UnknownBackendException):
            Simulation().reset()
            sim = Simulation()
            sim.backend = "fake_backend"
