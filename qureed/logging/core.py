import logging
from qureed.logging.loggers import LoggerCategory
from qureed.logging.formatter import SimulationTimeFormatter
from qureed.logging.hook import HookHandler, get_global_hook


def setup_logger(
    category: LoggerCategory, *, level=logging.INFO, use_hook=True, fmt=None
):
    """
    Configures and returns a logger for the specified logger category.

    This functions sets up a logger with both a console and stream handler and
    optional hook handler (e.g., for UI streaming or custom log sinks). It
    ensures that handlers are not duplicated, even when called multiple times
    for the same category.

    Arguments:
    ----------
    category : `LoggerCategory`
        The logging category (e.g., GLOBAL, DEVICES, SIMULATION). Determines
        the logger name used internally.
    level : `Optional[int]`
        The logging level (default is `logging.INFO`). Use `logging.DEBUG` for
        verbose output `logging.WARNING` for minimal logs.
    use_hook : `Optional[bool]`
        If True (default), attaches a `HookHandler` if a global logging hook
        if configured via `set_logging_hook`. THis enables external consumers
        (e.g., GUIs) to receive structured log messages.
    fmt: `Optional[str]`
        Custom log format string. If not provided, defaults to
        `"(simtime)s | %(message)s" and includes simulation time.

    Returns:
    --------
    logger : logging.Logger
        A configured logger instance for the given category.

    Examples:
    ---------
    >>> logger = setup_logger(LoggerCategory.GLOBAL, level=logging.DEBUG)
    >>> logger.info("Simulation Started")
    >>> logger.debug("Detailed event log")
    """
    logger = logging.getLogger(category.logger_name)
    if not logger.handlers:
        logger.setLevel(level)

    # console
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        ch = logging.StreamHandler()
        ch.setLevel(level)
        ch.setFormatter(
            SimulationTimeFormatter(fmt or "%(simtime)s | %(message)s")
        )
        logger.addHandler(ch)

    # hook
    if (
        use_hook
        and get_global_hook()
        and not any(isinstance(h, HookHandler) for h in logger.handlers)
    ):
        hh = HookHandler()
        hh.setLevel(level)
        hh.setFormatter(
            SimulationTimeFormatter(fmt or "%(simtime)s | %(message)s")
        )
        logger.addHandler(hh)

    return logger
