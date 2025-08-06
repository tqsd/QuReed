import unittest
from unittest.mock import patch

from qureed.simulation import Simulation
from qureed.devices.detectors.imperfect_detector import ImperfectDetector
from qureed.signals import IntSignal


class TestImperfectDetector(unittest.TestCase):
    def setUp(self):
        self.detector = ImperfectDetector()
        self.detector.set_property(
            "darkCountRateHz", 1e9
        )  # 1 GHz dark count rate (very high for test)
        self.detector.set_property(
            "deadTime", 0.0
        )  # disable dead time for this test
        self.env = self.detector.sim_env
        self.out_signals = []

        # Monkey patch `send` to capture outputs
        self.detector.send = lambda port, signal: self.out_signals.append(
            (port, signal, self.env.now)
        )

    def tearDown(self):
        Simulation.reset()

    def test_dark_counts_generated(self):
        self.env.process(self.detector.dark_count_proc())
        self.env.run(until=1e-8)  # Run for 10 ns

        self.assertTrue(
            any(sig.value > 0 for _, sig, _ in self.out_signals),
            "No dark counts detected",
        )
        self.assertGreaterEqual(
            len(self.out_signals), 1, "Expected at least one dark count"
        )

    def test_dead_time_suppresses(self):
        self.detector.set_property("deadTime", 5e-9)  # 5 ns dead time
        self.detector.set_property("darkCountRateHz", 0.0)  # no dark counts

        def generate_signal(at_time):
            def inner():
                yield self.env.timeout(at_time)
                sig = IntSignal(value=1)
                self.detector.send_with_dark_time(sig)

            return inner

        self.env.process(generate_signal(1e-9)())
        self.env.process(generate_signal(2e-9)())  # within dead time
        self.env.process(generate_signal(7e-9)())  # after dead time

        self.env.run(until=10e-9)
        self.assertEqual(
            len(self.out_signals),
            2,
            "Expected only two signals due to dead time suppression",
        )


if __name__ == "__main__":
    unittest.main()
