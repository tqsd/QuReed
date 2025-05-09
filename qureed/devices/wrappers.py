import functools
import types
from typing import Callable

from qureed.backends import _BACKENDS, UnknownBackendException

def des_proc(method=None, *, backend=None):
    """
    Decorator for registering a SimPy generator method as a DES process.

    Wraps an instance method so that:

    - It checks that the method returns a Python generator (SimPy coroutine).
    - It sets a flag `_is_des_process = True` on the wrapper, so that
      `GenericDevice`’s metaprocessor can discover and register it.

    Example
    -------
    >>> class MyDevice(GenericDevice):
    >>>     @des_proc(backend="photon_weave")
    >>>     def proc(self):
    ...         # This must be a generator yielding SimPy events
    ...         while True:
    ...             yield self.sim_env.timeout(1)
    ...             self.log_message("tick")
    >>>
    >>> dev = MyDevice()
    >>> # MyDevice.__init__ will see `_is_des_process` and do:
    >>> # self.sim_env.process(dev.proc())

    Parameters
    ----------
    method : function
        An instance method that should return a generator yielding SimPy events.

    Returns
    -------
    wrapper : function
        A function with the same signature as `method` that:
        - Calls the original `method`
        - Verifies the return is a `types.GeneratorType`
        - Raises `TypeError` if not
        - Carries the attribute `_is_des_process = True`

    Raises
    ------
    TypeError
        If the decorated method does not return a generator.
    """
    def decorate(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            gen = func(self, *args, *kwargs)
            if not isinstance(gen, types.GeneratorType):
                raise TypeError(
                    f"{self.__class__.__name__}.{method.__name__} "
                    "is not a generator. Generator Required"
                )
            return gen
        wrapper._is_des_process = True
        wrapper._supported_backend = backend
        return wrapper
    
    if method is None:
        # Called as @des_proc(backend=...)
        return decorate
    else:
        return decorate(method)
