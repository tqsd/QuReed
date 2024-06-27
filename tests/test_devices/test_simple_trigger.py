import random
import unittest

from qureed.devices.control import SimpleTrigger
from qureed.signals import GenericBoolSignal, GenericTimeSignal
from qureed.simulation.simulation import Simulation

from .helpers import get_unwrapped


class TestSimpleTrigger(unittest.TestCase):
    def test_init(self):
        trigger = SimpleTrigger("Simple Trigger")
        self.assertTrue("time" in trigger.ports)
        self.assertTrue("trigger" in trigger.ports)
        self.assertEqual(trigger.time, 0)

    def test_des_time_given(self):
        time = random.uniform(1, 10)
        trigger = SimpleTrigger("Simple Trigger")
        time_signal = GenericTimeSignal()
        time_signal.set_time(time)

        # Grab undecorated functions
        des_action = get_unwrapped(trigger.des_action)
        des = get_unwrapped(trigger.des)

        signals = {"signals": {"time": time_signal}}

        result = des(trigger, time=-1, **signals)
        self.assertIsNone(result)
        self.assertEqual(trigger.time, time)

        result = des_action(trigger, time=None)
        self.assertIsNone(result)

        result = des_action(trigger, time=0, **{"signals": {}})
        self.assertIsNone(result)

        result = des(trigger, time=0.5, **{"signals": {}})
        self.assertIsNone(result)

        result = des(trigger, time=time, **{"signals": {}})
        self.assertTrue("trigger" in result[0])
        self.assertTrue(time in result[0])
        self.assertTrue(result[0][1].contents)

    def test_des_time_not_given(self):
        time = random.uniform(1, 10)
        trigger = SimpleTrigger("Simple Trigger")
        simulation = Simulation.get_instance()
        self.assertEqual(simulation.event_queue[0].event_time, 0)
        self.assertTrue(simulation.event_queue[0].device, trigger)
        self.assertTrue(simulation.event_queue[0].args == ())
        self.assertTrue(simulation.event_queue[0].kwargs == {"signals": {}})

        des = get_unwrapped(trigger.des)
        result = des(trigger, time=time, **{"signals": {}})
        self.assertIsNone(result)
        result = des(trigger, time=0, **{"signals": {}})
        self.assertTrue("trigger" in result[0])
        self.assertTrue(0 in result[0])
        self.assertTrue(result[0][1].contents)
