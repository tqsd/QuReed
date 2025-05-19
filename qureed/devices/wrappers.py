import functools
import types

from qureed.backends import _BACKENDS, UnknownBackendException
from qureed.logging import setup_logger
from qureed.logging.loggers import LoggerCategory


def _wrap_and_log_process(self, gen, name):
    """
    Flatten a generator that may yield sub-generators (like any_receive),
    log every real SimPy Event it emits, and return a new generator.
    """
    logger = setup_logger(LoggerCategory.GLOBAL)
    def wrapped():
        result = None
        try:
            while True:
                yielded = gen.send(result)

                # Flatten sub-generators
                if isinstance(yielded, types.GeneratorType):
                    subgen = yielded
                    subres = None
                    try:
                        while True:
                            ev = subgen.send(subres)
                            meta = getattr(ev, "_des_meta", None)
                            desc = f"{type(ev).__name__} ({meta})" if meta else type(ev).__name__
                            logger.debug(f"{name} yielded (sub): {desc}")
                            subres = yield ev
                    except StopIteration as stop:
                        result = stop.value
                        continue

                # Normal SimPy Event
                meta = getattr(yielded, "_des_meta", None)
                desc = f"{type(yielded).__name__} ({meta})" if meta else type(yielded).__name__
                #print("SHOULD LOG")
                #print(f"{name} -> {desc}")
                logger.debug(f"{name} -> {desc}")
                result = yield yielded

        except StopIteration:
            logger.debug(f"{name} completed")

    return wrapped()



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
            proc_name = f"{self.__class__.__name__}.{func.__name__}"
            return _wrap_and_log_process(self, gen, proc_name)

        wrapper._is_des_process = True
        wrapper._supported_backend = backend
        return wrapper

    if method is None:
        # Called as @des_proc(backend=...)
        return decorate
    else:
        return decorate(method)
