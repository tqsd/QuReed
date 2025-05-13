import unittest
import math

from qureed.signals.quantum_optical_pulse_signal import (
    QuantumOpticalPulseSignal,
)
from qureed.simulation import Simulation
from qureed.devices.phase_shifters import IdealPhaseShifter

from photon_weave.state.envelope import Envelope


class DummyFock:
    def __init__(self):
        self.operations_applied = []

    def apply_operation(self, op):
        self.operations_applied.append(op)


class DummyEnvelope:
    def __init__(self):
        self.fock = DummyFock()


class TestIdealPhaseShifter(unittest.TestCase):
    def setUp(self):
        self.device = IdealPhaseShifter()
        self.sim_env = self.device.sim_env
        self.device.set_property("phi", math.pi)

    def tearDorn(self):
        Simulation.reset()

    def test_ports_and_properties(self):
        ports = self.device.port_definitions
        self.assertIn("input", ports)
        self.assertIn("output", ports)
        self.assertIn("phi", ports)

    def test_proc_pw(self):
        start_end_signals = []

        def capture_send(port, signal):
            start_end_signals.append((port, signal, self.sim_env.now))

        self.device.send = capture_send  # monkey patch send
        env = Envelope()
        env.fock.state = 1
        start_sig, end_sig = QuantumOpticalPulseSignal.create_pair(payload=env)

        def simulate_receive():
            yield self.sim_env.timeout(0)
            self.device.deliver(self.device.Ports.input, start_sig)
            yield self.sim_env.timeout(5e-9)
            self.device.deliver(self.device.Ports.input, end_sig)

        def assert_env_not_changed():
            yield self.sim_env.timeout(1e-9)
            self.assertEqual(env.fock.state, 1)

        self.sim_env.process(simulate_receive())
        self.sim_env.process(assert_env_not_changed())

        self.sim_env.run(until=1e-8)
        self.assertEqual(len(start_end_signals), 2)
        v = env.fock.state[1, 0]
        self.assertAlmostEqual(v.real, -1.0, places=6)
        self.assertAlmostEqual(v.imag, 0.0, places=6)


if __name__ == "__main__":
    unittest.main()
