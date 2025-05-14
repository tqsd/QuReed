import unittest
import math

from qureed.assets import icon_list
from qureed.devices.beam_splittters import GenericBeamSplitterDevice
from qureed.signals.quantum_optical_pulse_signal import (
    QuantumOpticalPulseSignal,
)


class DummyBeamSplitter(GenericBeamSplitterDevice):
    @property
    def gui_name(self) -> str:
        return "Dummy Beam-Splitter"


class TestGenericBeamSplitterDevice(unittest.TestCase):

    def test_properties(self):
        device = DummyBeamSplitter()
        self.assertEqual(device.get_property("eta"), math.pi / 4)
        device.set_property("eta", 1)
        self.assertEqual(device.get_property("eta"), 1)

    def test_ports(self):
        device = DummyBeamSplitter()
        ports = device.port_definitions
        self.assertIn("A", ports)
        self.assertEqual(ports["A"].direction, "input")
        self.assertEqual(ports["A"].signal_type, QuantumOpticalPulseSignal)
        self.assertIn("B", ports)
        self.assertEqual(ports["B"].direction, "input")
        self.assertEqual(ports["B"].signal_type, QuantumOpticalPulseSignal)
        self.assertIn("C", ports)
        self.assertEqual(ports["C"].direction, "output")
        self.assertEqual(ports["C"].signal_type, QuantumOpticalPulseSignal)
        self.assertIn("D", ports)
        self.assertEqual(ports["D"].direction, "output")
        self.assertEqual(ports["D"].signal_type, QuantumOpticalPulseSignal)

    def test_gui_icon(self):
        device = DummyBeamSplitter()
        self.assertEqual(device.gui_icon, icon_list.BEAM_SPLITTER)
