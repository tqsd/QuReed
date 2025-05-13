import unittest
import simpy

from qureed.simulation import Simulation
from qureed.devices.clocks.constant_clock import ConstantClock


class Receiver:
    """A simple receiver to collect signals for testing."""

    def __init__(self, env):
        self.env = env
        self.inbox = []
        self.store = simpy.Store(env)

    def deliver(self, port, signal):
        self.inbox.append((self.env.now, signal))
        self.store.put(signal)

    def run(self):
        while True:
            yield self.store.get()


class TestConstantClock(unittest.TestCase):
    def tearDown(self) -> None:
        Simulation.reset()

    def test_emits_ticks_at_constant_rate(self):
        env = simpy.Environment()
        clock = ConstantClock()
        receiver = Receiver(env)

        # Configure clock
        clock.set_property("frequency", 2.0)  # 2 Hz → every 0.5s
        clock.sim_env = env  # override environment
        clock._inboxes = {"tick": simpy.Store(env)}  # mock inbox
        clock._connected_ports["tick"] = type(
            "Connnection",
            (),
            {"get_next_device_and_port": lambda s: (receiver, "tick")},
        )()

        # Register the process
        env.process(clock.proc())

        # Run the simulation for 2.1s
        env.run(until=2.1)

        # Expect ~4 ticks at 0.0, 0.5, 1.0, 1.5
        self.assertEqual(len(receiver.inbox), 5)

        # Check that timestamps are roughly correct
        expected_times = [0.0, 0.5, 1.0, 1.5, 2.0]
        actual_times = [round(t, 2) for t, _ in receiver.inbox]
        self.assertEqual(actual_times, expected_times)


if __name__ == "__main__":
    unittest.main()
