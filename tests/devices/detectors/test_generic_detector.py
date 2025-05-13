import unittest

from qureed.devices import GenericDetectorDevice, des_proc
from qureed.signals import IntSignal, QuantumOpticalPulseSignal


class DummyDetector(GenericDetectorDevice):
    @property
    def gui_name(self) -> str:
        return "Dummy Detector"

    @des_proc
    def dummy_process(self):
        yield self.sim_env.timeout(1)


class TestGenericDetectorDevice(unittest.TestCase):
    def setUp(self):
        self.device = DummyDetector()

    def test_ports_are_defined(self):
        self.assertIn("input", self.device.port_definitions)
        self.assertIn("output", self.device.port_definitions)

        input_port = self.device.port_definitions["input"]
        output_port = self.device.port_definitions["output"]

        self.assertEqual(input_port.direction, "input")
        self.assertEqual(output_port.direction, "output")
        self.assertIs(input_port.signal_type, QuantumOpticalPulseSignal)
        self.assertIs(output_port.signal_type, IntSignal)

    def test_gui_icon(self):
        self.assertIsInstance(self.device.gui_icon, str)
        self.assertTrue(self.device.gui_icon.endswith(".png"))

    def test_ports_enum(self):
        self.assertEqual(self.device.Ports.input.value, "input")
        self.assertEqual(self.device.Ports.output.value, "output")
