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
        self.assertEqual(device._buffer, {})
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

    def test__store_and_send_starts(self):
        Simulation().reset()
        device = PerfectOverlapBeamSplitter()

        env = Envelope()
        sigA, _ = QuantumOpticalPulseSignal.create_pair(
            payload=env, metadata={"central_wavelength": 1550e-9}
        )
        sigB, _ = QuantumOpticalPulseSignal.create_pair(
            payload=env, metadata={"central_wavelength": 1550e-9}
        )

        wl = 1550e-9
        starts = {wl: {device.Ports.A: sigA, device.Ports.B: sigB}}

        sent = []

        def mock_send(local_port, signal):
            sent.append((local_port, signal))

        def mock_send_with_delay(port, signal):
            sent.append((port, signal))

        device.send = mock_send
        device._send_with_delay = mock_send_with_delay
        device._store_and_send_starts(starts)

        self.assertEqual(len(device._buffer), 1)
        entry = device._buffer[(0, wl)]
        self.assertIn(device.Ports.A, entry["starts"])
        self.assertIn(device.Ports.B, entry["starts"])
        self.assertEqual(entry["ends"], {})
        sent_signals = {id(s) for _, s in sent}
        self.assertIn(id(sigA), sent_signals)
        self.assertIn(id(sigB), sent_signals)

    def test__extract_starts(self):
        Simulation().reset()
        device = PerfectOverlapBeamSplitter()

        envA = Envelope()
        envB = Envelope()
        envC = Envelope()
        sigA = QuantumOpticalPulseSignal(
            payload=envA,
            metadata={"central_wavelength": 1550e-9},
            type=QOPSignalType.START,
        )
        sigB = QuantumOpticalPulseSignal(
            payload=envB,
            metadata={"central_wavelength": 1550e-9},
            type=QOPSignalType.START,
        )
        sig_end = QuantumOpticalPulseSignal(
            payload=envC,
            metadata={"central_wavelength": 1550e-9},
            type=QOPSignalType.END,
        )

        received = [
            (sigA, device.Ports.A),
            (sigB, device.Ports.B),
            (sig_end, device.Ports.A),
        ]

        result = device._extract_starts(received)

        self.assertEqual(len(result), 1)
        self.assertIn(1550e-9, result)

        ports_dict = result[1550e-9]
        self.assertEqual(len(ports_dict), 2)
        self.assertIs(ports_dict[device.Ports.A], sigA)
        self.assertIs(ports_dict[device.Ports.B], sigB)

    def test__complete_mising_starts(self):
        Simulation().reset()
        device = PerfectOverlapBeamSplitter()
        env = Envelope()
        sigA = QuantumOpticalPulseSignal(
            payload=env,
            metadata={"central_wavelength": 1550e-9},
            type=QOPSignalType.START,
        )
        starts = {1550e-9: {device.Ports.A: sigA}}

        new_starts = device._complete_missing_starts(starts)

        self.assertTrue(device.Ports.B in new_starts[1550e-9].keys())
        self.assertEqual(
            new_starts[1550e-9][device.Ports.B].metadata["central_wavelength"],
            1550e-9,
        )
        self.assertIsInstance(
            new_starts[1550e-9][device.Ports.B].payload, Envelope
        )
        self.assertIsNot(new_starts[1550e-9][device.Ports.B].payload, env)
        self.assertIs(new_starts[1550e-9][device.Ports.A], sigA)

    def test_operation_single_envelope(self):
        Simulation().reset()
        device = PerfectOverlapBeamSplitter()

        produced_signals = []

        def mock_send(port, signal):
            produced_signals.append((port, signal))

        device._send_with_delay = mock_send

        env = Envelope()
        env.fock.state = 1
        sig_start, sig_end = QuantumOpticalPulseSignal.create_pair(
            payload=env, metadata={"central_wavelength": 1550e-9}
        )

        def signal_feed():
            device.deliver(device.Ports.A, sig_start)
            yield Simulation().simpy_env.timeout(5e-9)
            device.deliver(device.Ports.A, sig_end)

        Simulation().simpy_env.process(signal_feed())
        Simulation().run(until=1e-8)
        # print(produced_signals)
        self.assertEqual(len(produced_signals), 4)

        env1 = produced_signals[0][1].payload
        env2 = produced_signals[1][1].payload

        state = env1.composite_envelope.states[0].state.flatten()
        dim2 = env2.fock.dimensions

        idx_01 = 1
        idx_10 = 1 * dim2 + 0

        target = 1 / math.sqrt(2)
        self.assertAlmostEqual(abs(state[idx_10]), target, places=7)
        self.assertAlmostEqual(abs(state[idx_01]), target, places=7)

        for i, amp in enumerate(state):
            if i not in (idx_10, idx_01):
                self.assertAlmostEqual(abs(amp), 0.0, places=7)

        self.assertEqual(device._buffer, {})

    def test_operation_two_envelopes(self):
        Simulation().reset()
        device = PerfectOverlapBeamSplitter()

        produced_signals = []

        def mock_send(port, signal):
            produced_signals.append((port, signal))

        device._send_with_delay = mock_send

        env1 = Envelope()
        env1.fock.state = 1
        env2 = Envelope()
        env2.fock.state = 1
        sig1_start, sig1_end = QuantumOpticalPulseSignal.create_pair(
            payload=env1, metadata={"central_wavelength": 1550e-9}
        )
        sig2_start, sig2_end = QuantumOpticalPulseSignal.create_pair(
            payload=env2, metadata={"central_wavelength": 1550e-9}
        )

        def signal_feed():
            device.deliver(device.Ports.A, sig1_start)
            device.deliver(device.Ports.B, sig2_start)
            yield Simulation().simpy_env.timeout(5e-9)
            device.deliver(device.Ports.A, sig1_end)
            device.deliver(device.Ports.B, sig2_end)

        Simulation().simpy_env.process(signal_feed())
        Simulation().run(until=1e-8)
        # print(produced_signals)
        self.assertEqual(len(produced_signals), 4)

        env1 = produced_signals[0][1].payload
        env2 = produced_signals[1][1].payload

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
        self.assertEqual(device._buffer, {})
