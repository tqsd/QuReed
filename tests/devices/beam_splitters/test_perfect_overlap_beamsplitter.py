import unittest
import math

from qureed.devices.beam_splittters import PerfectOverlapBeamSplitter
from qureed.signals.quantum_optical_pulse_signal import QOPSignalType
from qureed.simulation.simulation import Simulation
from qureed.assets import icon_list
from qureed.signals import QuantumOpticalPulseSignal

from photon_weave.state.envelope import Envelope


class TestPerfectOverlapBeamSplitter(unittest.TestCase):
    def setUp(self):
        Simulation().reset()

    def tearDown(self) -> None:
        Simulation().reset()

    def test_init(self):
        device = PerfectOverlapBeamSplitter()
        self.assertEqual(device._buffer, [])
        self.assertEqual(device.delay, 1.5e-10)

    def test_gui_metadata(self):
        device = PerfectOverlapBeamSplitter()
        self.assertEqual(device.gui_icon, icon_list.BEAM_SPLITTER)
        self.assertEqual(device.gui_name, "Perfect Overlap Beam Splitter")

    def test_port_translation(self):
        device = PerfectOverlapBeamSplitter()
        self.assertIs(device._port_translation(device.Ports.A), device.Ports.C)
        self.assertIs(device._port_translation(device.Ports.B), device.Ports.D)

    def test__genrate_signals(self):
        with self.assertRaises(NotImplementedError):
            device = PerfectOverlapBeamSplitter()
            Simulation()._backend = "Backend"
            test_sig, _ = QuantumOpticalPulseSignal.create_pair(payload=None)
            device._generate_signals(test_sig)
        Simulation().reset()

        device = PerfectOverlapBeamSplitter()
        test_sig, _ = QuantumOpticalPulseSignal.create_pair(
            payload=3.14, metadata={"value": "random"}
        )
        start_sig, end_sig = device._generate_signals(test_sig)
        self.assertIsNot(test_sig, start_sig)
        self.assertIsNot(test_sig, end_sig)
        self.assertEqual(test_sig.metadata, start_sig.metadata)
        self.assertEqual(test_sig.metadata, end_sig.metadata)
        self.assertIsInstance(start_sig.payload, Envelope)
        self.assertIsInstance(end_sig.payload, Envelope)
        self.assertIs(start_sig.payload, end_sig.payload)

    def test__mixing_process(self):
        with self.assertRaises(NotImplementedError):
            device = PerfectOverlapBeamSplitter()
            Simulation()._backend = "Backend"
            test_sig_start, test_sig_end = (
                QuantumOpticalPulseSignal.create_pair(payload=None)
            )
            device._mixing_process(test_sig_start, test_sig_end)

    def test__mixing_process_photon_weave(self):
        Simulation().reset()
        device = PerfectOverlapBeamSplitter()
        env1 = Envelope()
        env1.fock.state = 1
        env2 = Envelope()
        env2.fock.state = 1
        sig1 = QuantumOpticalPulseSignal(payload=env1, type=QOPSignalType.END)
        sig2 = QuantumOpticalPulseSignal(payload=env2, type=QOPSignalType.END)

        device._mixing_process(sig1, sig2)

        state = env1.composite_envelope.states[0].state.flatten()

        dim2 = env2.fock.dimensions

        idx_02 = 2
        idx_20 = 2 * dim2 + 0

        target = 1 / math.sqrt(2)
        self.assertAlmostEqual(abs(state[idx_20]), target, places=7)
        self.assertAlmostEqual(abs(state[idx_02]), target, places=7)

        for i, amp in enumerate(state):
            if i not in (idx_20, idx_02):
                self.assertAlmostEqual(abs(amp), 0.0, places=7)
