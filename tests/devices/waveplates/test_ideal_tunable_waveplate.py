import unittest
import math

from photon_weave.state.envelope import Envelope
from photon_weave.state.polarization import PolarizationLabel

from qureed.devices.waveplates import IdealTunableWaveplate
from qureed.signals.quantum_optical_pulse_signal import (
    QuantumOpticalPulseSignal,
)
from qureed.signals.value_signals import FloatSignal
from qureed.simulation.simulation import Simulation


class TestTunable(unittest.TestCase):
    def setUp(self):
        Simulation().reset()

    def tearDown(self):
        Simulation().reset()

    def test_photon_weave(self):
        device = IdealTunableWaveplate()

        produced_signals = []

        def mock_send(signal):
            produced_signals.append(signal)

        device._send_with_delay = mock_send
        env = Envelope()
        signal_start, signal_end = QuantumOpticalPulseSignal.create_pair(
            payload=env
        )
        control_signal = FloatSignal(value=math.pi)

        def signal_feed():
            device.deliver(device.Ports.control, control_signal)
            yield Simulation().simpy_env.timeout(1e-5)
            device.deliver(device.Ports.input, signal_start)
            yield Simulation().simpy_env.timeout(5e-9)
            device.deliver(device.Ports.input, signal_end)

        Simulation().simpy_env.process(signal_feed())
        Simulation().simpy_env.run(until=1)

        self.assertTrue(len(produced_signals), 2)
        self.assertIs(
            produced_signals[0].payload.polarization.state, PolarizationLabel.V
        )
        self.assertIs(
            produced_signals[1].payload.polarization.state, PolarizationLabel.V
        )
