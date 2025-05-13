import unittest

from qureed.simulation import Simulation
from qureed.devices import IdealNPhotonSource
from qureed.signals import IntSignal, TriggerSignal, QuantumOpticalPulseSignal


class TestIdealNPhotonSource(unittest.TestCase):
    def setUp(self):
        self.device = IdealNPhotonSource()
        self.env = self.device.sim_env

    def tearDown(self):
        Simulation.reset()

    def test_port_definitions(self):
        ports = self.device.port_definitions
        self.assertIn("output", ports)
        self.assertIn("photon_num", ports)
        self.assertIn("trigger", ports)
        self.assertEqual(
            ports["output"].signal_type, QuantumOpticalPulseSignal
        )
        self.assertEqual(ports["output"].direction, "output")
        self.assertEqual(ports["photon_num"].signal_type, IntSignal)
        self.assertEqual(ports["photon_num"].direction, "input")
        self.assertEqual(ports["trigger"].signal_type, TriggerSignal)
        self.assertEqual(ports["trigger"].direction, "input")

    def test_default_properties(self):
        self.assertEqual(self.device.get_property("photonNum"), 1)
        self.assertEqual(
            self.device.get_property("centralWavelength"), 1550e-9
        )
        self.assertEqual(self.device.get_property("pulseDuration"), 1e-9)

    def test_photon_num_proc_updates_property(self):
        new_signal = IntSignal(value=5)
        new_signal.timestamp = 0.0
        new_signal.sender = self.device

        self.device._inboxes["photon_num"].put(new_signal)
        self.env.process(self.device.photon_num_proc())
        self.env.run(until=self.env.now + 0.1)

        self.assertEqual(self.device.get_property("photonNum"), 5)

    def test_proc_pw_emits_start_and_end(self):
        start_end_signals = []

        def capture_send(port, signal):
            start_end_signals.append((port, signal))

        self.device.send = capture_send  # monkey patch send

        self.device.set_property("photonNum", 3)

        # Send a trigger
        self.device._inboxes["trigger"].put(TriggerSignal())
        self.env.process(self.device.proc_pw())
        self.env.run(until=self.env.now + 1e-8)

        self.assertEqual(len(start_end_signals), 2)
        self.assertEqual(start_end_signals[0][1].type.name, "START")
        self.assertEqual(start_end_signals[1][1].type.name, "END")

        start_payload = start_end_signals[0][1].payload
        self.assertEqual(start_payload.fock.state, 3)
