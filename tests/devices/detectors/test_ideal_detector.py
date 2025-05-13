import unittest

from qureed.simulation import Simulation
from qureed.devices import IdealDetector
from qureed.signals import IntSignal, QuantumOpticalPulseSignal


class DummyEnvelope:
    def __init__(self, fock_value=1, pol_value="H"):
        self.fock = "fock"
        self.polarization = "polarization"
        self._fock_value = fock_value
        self._pol_value = pol_value

    def measure(self):
        return {
            self.fock: self._fock_value,
            self.polarization: self._pol_value,
        }


class TestIdealDetector(unittest.TestCase):
    def tearDown(self) -> None:
        Simulation.reset()

    def setUp(self):
        self.detector = IdealDetector()
        self.detector.set_property("delay", 2e-9)
        self.env = self.detector.sim_env

    def test_ports_defined(self):
        ports = self.detector.port_definitions
        self.assertIn("input", ports)
        self.assertIn("output", ports)
        self.assertEqual(ports["input"].direction, "input")
        self.assertEqual(ports["output"].direction, "output")
        self.assertIs(ports["input"].signal_type, QuantumOpticalPulseSignal)
        self.assertIs(ports["output"].signal_type, IntSignal)

    def test_delay_property(self):
        self.assertAlmostEqual(self.detector.get_property("delay"), 2e-9)

    def test_proc_pw(self):
        detected_signals = []

        def capture_send(port, signal):
            detected_signals.append((port, signal, self.detector.sim_env.now))

        dummy_env = DummyEnvelope(fock_value=3, pol_value="V")
        start_signal, end_signal = QuantumOpticalPulseSignal.create_pair(
            payload=dummy_env
        )
        self.detector.send = capture_send  # monkey patch send

        def signal_feeder():
            yield self.env.timeout(0)
            self.detector._inboxes["input"].put(start_signal)
            yield self.env.timeout(1e-9)
            self.detector._inboxes["input"].put(end_signal)

        self.env.process(signal_feeder())
        self.env.run(until=1e-6)

        self.assertEqual(len(detected_signals), 1)
        self.assertIs(detected_signals[0][0], self.detector.Ports.output)
        self.assertIsInstance(detected_signals[0][1], IntSignal)
        self.assertEqual(detected_signals[0][1].value, 3)
        polarization = detected_signals[0][1].metadata.get(
            "polarization", "False"
        )
        self.assertAlmostEqual(detected_signals[0][2], 3e-9)
        self.assertEqual(polarization, "V")
