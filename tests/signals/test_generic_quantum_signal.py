import unittest
from qureed.signals import GenericQuantumSignal

class TestGenericQuantumSignal(unittest.TestCase):
    def test_default_initialization(self):
        signal = GenericQuantumSignal()
        self.assertIsNone(signal.timestamp)
        self.assertIsNone(signal.sender)
        self.assertEqual(signal.metadata, {})
        self.assertIsNone(signal.payload)

    def test_custom_initialization(self):
        dummy_payload = {"quantum_state": "some_state"}
        dummy_sender = object()
        metadata = {"type": "quantum"}
        signal = GenericQuantumSignal(
            timestamp=42.0,
            sender=dummy_sender,
            metadata=metadata,
            payload=dummy_payload
            )

        self.assertEqual(signal.timestamp, 42.0)
        self.assertIs(signal.sender, dummy_sender)
        self.assertEqual(signal.metadata, metadata)
        self.assertIs(signal.payload, dummy_payload)

    def test_repr(self):
        signal = GenericQuantumSignal(timestamp=1.0, metadata={"a": 1}, payload="test")
        self.assertIn("GenericQuantumSignal", repr(signal))
        self.assertIn("ts=1.0", repr(signal))
        self.assertIn("metadata={'a': 1}", repr(signal))
