import unittest

from simpy import Store

from qureed.simulation import Simulation
from qureed.devices import GenericDevice, des_proc, Port
from qureed.signals import GenericQuantumSignal
from qureed.devices.exceptions import PortDirectionException

class DummySignal(GenericQuantumSignal):
    pass

class DummyDevice(GenericDevice):

    properties = {
        "dummy_property": {
            "type": int,
            }
        }

    port_definitions = {
        "input": Port(
            direction="input",
            signal_type=GenericQuantumSignal
            ),
        "output": Port(
            direction="output",
            signal_type=GenericQuantumSignal
            ),
        "in": Port(
            direction="input",
            signal_type=DummySignal
            )
        }

    reference = None
    gui_name = "DummyDevice"
    gui_icon = None
    

    @des_proc(backend="photon_weave")
    def proc(self):
        while True:
            signal = yield self.receive("input")
            yield self.sim_env.timeout(1)
            self.send(self.Ports.output, signal)


class DummySource(GenericDevice):

    properties = {
        "dummy_property": {
            "type": int,
            }
        }


    port_definitions = {
        "output": Port(
            direction="output",
            signal_type=GenericQuantumSignal
            )
        }

    reference = None
    gui_name = "DummySource"
    gui_icon = None
    

    @des_proc(backend="photon_weave")
    def proc(self):
        while True:
            yield self.sim_env.timeout(1)
            signal = GenericQuantumSignal()
            self.send(self.Ports.output, signal)

class MultiPortDevice(GenericDevice):
    port_definitions = {
        "in1": Port(direction="input", signal_type=GenericQuantumSignal),
        "in2": Port(direction="input", signal_type=GenericQuantumSignal),
    }

    gui_name = "MultiPortDevice"
    gui_icon = None
    reference = None

    @des_proc(backend="photon_weave")
    def proc(self):
        while True:
            yield self.sim_env.timeout(10)


class TestDeviceInitialization(unittest.TestCase):
    def test_initialization(self):
        device = DummySource()
        
        self.assertIsNotNone(device.uid)
        self.assertTrue(hasattr(device, "sim_env"))
        self.assertTrue(hasattr(device, "logger"))
        self.assertIn("name", device.properties)
        self.assertIsNone(device.get_property("name"))

        device.set_property("name", "TestDevice")
    
        self.assertEqual(device.properties["name"]["value"], "TestDevice")
        self.assertEqual(device.get_property("name"), "TestDevice")

    def test_ports_existence_and_enum(self):
        device = DummyDevice()

        self.assertIn("input", device.ports)
        self.assertIn("output", device.ports)
        self.assertTrue(isinstance(device.ports["input"], Port))
        self.assertTrue(isinstance(device.ports["output"], Port))

        self.assertTrue(hasattr(DummyDevice, "Ports"))
        self.assertEqual(DummyDevice.Ports.input.value, "input")
        self.assertEqual(DummyDevice.Ports.output.value, "output")

    def test_inboxes_connected_ports_initiation(self):
        device = DummyDevice()

        self.assertIsNotNone(device._connected_ports)
        self.assertIsNotNone(device._inboxes)

        for port in ["input", "output", "in"]:
            self.assertIn(port, device._connected_ports)
            self.assertIsNone(device._connected_ports[port])
            self.assertTrue(isinstance(
                device._inboxes[port],
                Store
                ))

class TestPropertyHandling(unittest.TestCase):
    def test_get_property(self):
        device = DummySource()
        self.assertIsNone(device.get_property("name"))
        self.assertIsNone(device.get_property("dummy_property"))

    def test_set_property(self):
        device = DummySource()
        self.assertIsNone(device.get_property("name"))
        self.assertIsNone(device.get_property("dummy_property"))
        device.set_property("name", "test_property")
        device.set_property("dummy_property", 42)
        self.assertEqual(
            device.get_property("name"),
            "test_property"
            )
        self.assertEqual(
            device.get_property("dummy_property"),
            42
            )

    def test_wrong_property_type(self):
        device = DummySource()
        with self.assertRaises(TypeError):
            device.set_property("dummy_property", "str_type")

    def test_wrong_property_name(self):
        device = DummySource()
        with self.assertRaises(AttributeError):
            device.set_property("wrong_property", "str_type")

class TestConnectionLogic(unittest.TestCase):
    def test_connect_connection(self):
        device1 = DummyDevice()
        device2 = DummyDevice()
        device1.connect(device1.Ports.output, device2, device2.Ports.input)
        connection = device1._connected_ports[device1.Ports.output.value]
        self.assertIsNotNone(connection)
        self.assertIs(
            connection,
            device2._connected_ports[device1.Ports.input.value]
            )
        self.assertIs(connection.source_device, device1)
        self.assertEqual(connection.source_port, device1.Ports.output.value)
        self.assertIs(connection.sink_device, device2)
        self.assertEqual(connection.sink_port, device2.Ports.input.value)

    def test_connect_exception(self):
        device1 = DummyDevice()
        device2 = DummyDevice()
        with self.assertRaises(PortDirectionException):
            device1.connect(device1.Ports.output, device2, device2.Ports.output)

    def test_correct_signal_type(self):
        device1 = DummyDevice()
        device2 = DummyDevice()
        device1.connect(device1.Ports.output, device2, device2.Ports["in"])
        connection = device1._connected_ports[device1.Ports.output.value]
        self.assertIs(connection.signal_type, GenericQuantumSignal)

class TestSendReceive(unittest.TestCase):
    def test_deliver_and_receive(self):
        device = DummyDevice()
        signal = GenericQuantumSignal()
        port = device.Ports.input
        device.deliver(port, signal)
        received_signal = device.sim_env.run(until=device.receive(port))
        self.assertIs(received_signal, signal)

    def test_send_and_deliver(self):
        sender = DummyDevice()
        receiver = DummyDevice()
        sender.connect(sender.Ports.output, receiver, receiver.Ports.input)

        signal = GenericQuantumSignal()

        sender.send(sender.Ports.output, signal)

        received_signal = receiver.sim_env.run(until=receiver.receive(receiver.Ports.input))
        self.assertIs(received_signal, signal)


class TestAnyReceive(unittest.TestCase):
    def test_any_receive_single_signal(self):
        device = MultiPortDevice()
        signal = GenericQuantumSignal()
        results = []

        def deliver_later():
            yield device.sim_env.timeout(0)
            device.deliver("in1", signal)

        def run_receive():
            received = yield from device.any_receive("in1", "in2")
            results.extend(received)

        device.sim_env.process(run_receive())
        device.sim_env.process(deliver_later())
        device.sim_env.run(until=20)

        self.assertEqual(len(results), 1)
        self.assertIs(results[0][0], signal)
        self.assertEqual(results[0][1], "in1")
