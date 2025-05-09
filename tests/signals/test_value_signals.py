import unittest
from mpmath import mpf, mpc
from qureed.signals import (
    BoolSignal,
    IntSignal,
    FloatSignal,
    ComplexSignal,
    StringSignal
)

class TestTypedSignals(unittest.TestCase):

    def test_signals(self):
        test_cases = [
            (BoolSignal, True),
            (IntSignal, 123),
            (FloatSignal, mpf("3.14")),
            (FloatSignal, 3.14),
            (ComplexSignal, mpc("1.0", "2.0")),
            (ComplexSignal, 1-1j),
            (StringSignal, "hello")
        ]

        for cls, val in test_cases:
            with self.subTest(cls=cls.__name__):
                s = cls(timestamp=0.0, value=val, metadata={"source": "test"})
                self.assertEqual(s.value, val)
                self.assertEqual(s.timestamp, 0.0)
                self.assertEqual(s.metadata, {"source": "test"})
                self.assertIn(cls.__name__, repr(s))
                self.assertIn("val=", repr(s))

if __name__ == "__main__":
    unittest.main()
