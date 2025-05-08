import types
import unittest
import inspect

from qureed.devices.wrappers import des_proc  # adjust import path

class Dummy:
    """Dummy class to attach decorated methods."""

    @des_proc
    def good_proc(self):
        """This is a good generator."""
        yield "tick"

    @des_proc
    def bad_proc(self):
        """This is not a generator."""
        return "not a generator"


class TestDesProcDecorator(unittest.TestCase):
    def test_metadata_preserved(self):
        # The wrapper should keep the original name and docstring
        self.assertEqual(Dummy.good_proc.__name__, "good_proc")
        self.assertEqual(Dummy.good_proc.__doc__, "This is a good generator.")

        # It should have our marker flag
        self.assertTrue(hasattr(Dummy.good_proc, "_is_des_process"))
        self.assertTrue(Dummy.good_proc._is_des_process)

    def test_good_proc_returns_generator(self):
        inst = Dummy()
        gen = inst.good_proc()                  # call the wrapper
        self.assertIsInstance(gen, types.GeneratorType)
        # And you can step through it
        self.assertEqual(next(gen), "tick")

    def test_bad_proc_raises_type_error(self):
        inst = Dummy()
        with self.assertRaises(TypeError) as cm:
            inst.bad_proc()
        # check that the error message mentions your class and method
        self.assertIn("Dummy.bad_proc is not a generator", str(cm.exception))

    def test_wrapper_is_not_marked_generatorfunction(self):
        # By design, inspect.isgeneratorfunction(wrapper) is False
        # because wrapper returns a generator, but isn't itself a generatordef.
        self.assertFalse(inspect.isgeneratorfunction(Dummy.good_proc))

if __name__ == "__main__":
    unittest.main()
