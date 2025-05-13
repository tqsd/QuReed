import unittest

from qureed.simulation import Simulation
from qureed.signals import QuantumOpticalPulseSignal, FloatSignal
from qureed.devices import GenericPhaseShifter


class DummyPhaseShifter(GenericPhaseShifter):
    """
    Minimal subclass to make GenericPhaseShifter
    instantaiable for testing
    """

    @property
    def gui_name(self) -> str:
        return "Dummy Phase Shifter"


class TestGenericPhaseShifter(unittest.TestCase):
    def setUp(self):
        self.device = DummyPhaseShifter()
        self.sim_env = self.device.sim_env

    def tearDown(self):
        Simulation.reset()

    def test_port_definitions(self):
        ports = self.device.port_definitions
        self.assertIn("input", ports)
        self.assertIn("output", ports)
        self.assertIn("phi", ports)
        self.assertEqual(ports["input"].direction, "input")
        self.assertEqual(ports["output"].direction, "output")
        self.assertEqual(ports["phi"].direction, "input")
        self.assertIs(ports["input"].signal_type, QuantumOpticalPulseSignal)
        self.assertIs(ports["output"].signal_type, QuantumOpticalPulseSignal)
        self.assertIs(ports["phi"].signal_type, FloatSignal)

    def test_default_phi_property(self):
        self.assertIsNone(self.device.get_property("phi"))

    def test_phi_proc_updates_property(self):
        def phi_sender():
            yield self.sim_env.timeout(0)
            float_signal = FloatSignal(value=3.1415)
            self.device._inboxes["phi"].put(float_signal)

        self.sim_env.process(phi_sender())
        self.sim_env.run(until=1)
        self.assertAlmostEqual(self.device.get_property("phi"), 3.1415)
