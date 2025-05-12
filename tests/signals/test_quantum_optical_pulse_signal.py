import unittest

from qureed.signals import QuantumOpticalPulseSignal, QOPSignalType


class TestQuantumOpticalPulseSignal(unittest.TestCase):
    def setUp(self):
        self.payload = {"mock": "state"}

    def test_create_pair_returns_two_instances(self):
        start, end = QuantumOpticalPulseSignal.create_pair(self.payload)
        self.assertIsInstance(start, QuantumOpticalPulseSignal)
        self.assertIsInstance(end, QuantumOpticalPulseSignal)
        self.assertIsNot(start, end)

    def test_pair_types_are_correct(self):
        start, end = QuantumOpticalPulseSignal.create_pair(self.payload)
        self.assertEqual(start.type, QOPSignalType.START)
        self.assertEqual(end.type, QOPSignalType.END)

    def test_pair_links_are_symmetric(self):
        start, end = QuantumOpticalPulseSignal.create_pair(self.payload)
        self.assertIs(start.pair, end)
        self.assertIs(end.pair, start)

    def test_shared_payload(self):
        start, end = QuantumOpticalPulseSignal.create_pair(self.payload)
        self.assertIs(start.payload, end.payload)
        self.assertIs(start.payload, self.payload)

    def test_pair_optional_when_constructed_directly(self):
        signal = QuantumOpticalPulseSignal(
            type=QOPSignalType.START, payload=self.payload
        )
        self.assertIsNone(signal.pair)
        self.assertEqual(signal.type, QOPSignalType.START)
        self.assertEqual(signal.payload, self.payload)


if __name__ == "__main__":
    unittest.main()
