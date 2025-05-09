import unittest

from qureed.signals import GenericValueSignal

class TestGenericValueSignal(unittest.TestCase):

    def test_default_initialization(self):
        signal = GenericValueSignal()
        self.assertIsNone(signal.timestamp)
        self.assertIsNone(signal.sender)
        self.assertEqual(signal.metadata, {})
        self.assertIsNone(signal.value)

    def test_custom_initialization(self):
        dummy_value = "dummy_value"
        dummy_sender = object()
        metadata = {"type": "quantum"}
        signal = GenericValueSignal(
            timestamp=42.0,
            sender=dummy_sender,
            metadata=metadata,
            value=dummy_value
            )

        self.assertEqual(signal.timestamp, 42.0)
        self.assertIs(signal.sender, dummy_sender)
        self.assertEqual(signal.metadata, metadata)
        self.assertIs(signal.value, dummy_value)

    def test_repr(self):
        dummy_value = "dummy_value"
        dummy_sender = object()
        metadata = {"type": "classical"}
        signal = GenericValueSignal(
            timestamp=42.0,
            sender=dummy_sender,
            metadata=metadata,
            value=dummy_value
            )
        repr_str = repr(signal)
        self.assertIn("GenericValueSignal", repr_str)
        self.assertIn("ts=42.0", repr_str)
        self.assertIn("val=dummy_value", repr_str)
        self.assertIn("metadata={'type': 'classical'}", repr_str)
