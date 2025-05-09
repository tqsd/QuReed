import unittest
from qureed.devices.clocks.generic_clock_device import GenericClockDevice
from qureed.devices import des_proc
from qureed.signals import TriggerSignal


class DummyClock(GenericClockDevice):

    @property
    def gui_name(self):
        return "Dummy Clock"

    @des_proc
    def proc(self):
        while False:
            yield


class TestGenericClockDevice(unittest.TestCase):
    def test_abstract_instantiation(self):
        with self.assertRaises(TypeError):
            GenericClockDevice()  # Cannot instantiate ABC directly

    def test_subclass_properties(self):
        clock = DummyClock()
        clock.set_property("frequency", 2.5)
        self.assertEqual(clock.get_property("frequency"), 2.5)

    def test_port_definitions(self):
        clock = DummyClock()
        ports = clock.ports
        self.assertIn("tick", ports)
        self.assertEqual(ports["tick"].direction, "output")
        self.assertEqual(ports["tick"].signal_type, TriggerSignal)

    def test_gui_icon(self):
        clock = DummyClock()
        self.assertEqual(clock.gui_icon, DummyClock().gui_icon)

    def test_repr(self):
        clock = DummyClock()
        self.assertIn("DummyClock", repr(clock))
        self.assertIn("uid=", repr(clock))

    def test_inbox_structure(self):
        clock = DummyClock()
        self.assertIn("tick", clock._inboxes)
        self.assertEqual(len(clock._inboxes), 1)
    
