import unittest

from qureed.devices.fibers.generic_fiber import GenericFiber
from qureed.signals.quantum_optical_pulse_signal import (
    QuantumOpticalPulseSignal,
)
from qureed.simulation.simulation import Simulation


class DummyFiber(GenericFiber):
    @property
    def gui_name(self) -> str:
        return "Dummy Fiber"


class TestGenericFiber(unittest.TestCase):
    def setUp(self) -> None:
        Simulation().reset()
        self.device = DummyFiber()

    def tearDown(self) -> None:
        Simulation().reset()

    def test_ports_are_defined(self):
        self.assertIn("input", self.device.port_definitions)
        self.assertIn("output", self.device.port_definitions)

        input_port = self.device.port_definitions["input"]
        output_port = self.device.port_definitions["output"]

        self.assertEqual(input_port.direction, "input")
        self.assertEqual(output_port.direction, "output")
        self.assertIs(input_port.signal_type, QuantumOpticalPulseSignal)
        self.assertIs(output_port.signal_type, QuantumOpticalPulseSignal)

    def test_gui_icon(self):
        self.assertIsInstance(self.device.gui_icon, str)
        self.assertTrue(self.device.gui_icon.endswith(".png"))

    def test_ports_enum(self):
        self.assertEqual(self.device.Ports.input.value, "input")
        self.assertEqual(self.device.Ports.output.value, "output")
