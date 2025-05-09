import unittest
from qureed.signals import GenericSignal

class MockSignal(GenericSignal):
    pass

class TestGenericSignal(unittest.TestCase):

    def test_default_initialization(self):
        signal = MockSignal()
        self.assertIsNone(signal.timestamp)
        self.assertIsNone(signal.sender)
        self.assertEqual(signal.metadata, {})

    def test_custom_initialization(self):
        metadata = {"type": "test", "value": 42}
        sender = object()
        signal = MockSignal(timestamp=10.5, sender=sender, metadata=metadata)
        self.assertEqual(signal.timestamp, 10.5)
        self.assertIs(signal.sender, sender)
        self.assertEqual(signal.metadata, metadata)

    def test_repr(self):
        signal = MockSignal(timestamp=1.25, metadata={"key": "val"})
        expected = "<MockSignal ts=1.25 metadata={'key': 'val'}>"
        self.assertEqual(repr(signal), expected)
