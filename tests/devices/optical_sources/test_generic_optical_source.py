import unittest

from qureed.devices import GenericOpticalSourceDevice, Port, GenericDevice
from qureed.signals import TriggerSignal
from qureed.assets import icon_list


class DummySource(GenericOpticalSourceDevice):
    @property
    def gui_name(self) -> str:
        return "DummySource"


class TestGenericOpticalSourceDevice(unittest.TestCase):
    def setUp(self):
        self.device = DummySource()

    def test_trigger_port_exists(self):
        self.assertIn("trigger", self.device.port_definitions)
        port = self.device.port_definitions["trigger"]
        self.assertIsInstance(port, Port)
        self.assertEqual(port.direction, "input")
        self.assertEqual(port.signal_type, TriggerSignal)

    def test_ports_enums(self):
        self.assertEqual(self.device.Ports.trigger.value, "trigger")

    def test_gui_icon(self):
        self.assertEqual(self.device.gui_icon, icon_list.N_PHOTON_SOURCE)

    def tests_inherits_generic_device(self):
        self.assertIsInstance(self.device, GenericDevice)


if __name__ == "__main__":
    unittest.main()
