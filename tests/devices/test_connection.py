import unittest
import dataclasses

from qureed.devices.connection import Connection, resolve_connection_direction
from qureed.devices.exceptions import PortDirectionException

class TestResolveConnectionDirection(unittest.TestCase):
    def test_resolve_output_to_input(self):
        A, B = object(), object()
        result = resolve_connection_direction(
            A, "p1", "output", B, "p2", "input"
            )
        self.assertEqual(
            result,
            (A, "p1", B, "p2")
            )

    def test_resolve_input_to_output(self):
        A, B = object(), object()
        result = resolve_connection_direction(
            A, "p1", "input", B, "p2", "output"
            )
        self.assertEqual(
            result,
            (B, "p2", A, "p1")
            )

    def test_resolve_invalid_direction_raises(self):
        with self.assertRaises(PortDirectionException):
            resolve_connection_direction(None, "p", "input", None, "q", "input")
        with self.assertRaises(PortDirectionException):
            resolve_connection_direction(None, "p", "output", None, "q", "output")
        with self.assertRaises(PortDirectionException):
            resolve_connection_direction(None, "p", "foo", None, "q", "bar")

class TestConnectionIntegrity(unittest.TestCase):
    def test_connection_frozen_and_fields(self):
        src = object()
        sink = object()
        c = Connection(
            source_device=src,
            source_port="out",
            sink_device=sink,
            sink_port="in",
            signal_type=int
            )

        self.assertIs(c.source_device, src)
        self.assertIs(c.sink_device, sink)
        self.assertEqual(c.source_port, "out")
        self.assertEqual(c.sink_port, "in")
        self.assertIs(c.signal_type, int)

        with self.assertRaises(dataclasses.FrozenInstanceError):
            c.source_port = "other"
