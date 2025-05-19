"""
Logging Hook Utilities for QuReed Simulation

This module provides utilities for enabling structured logging during
QuReed simulations. It allows:

- Attaching a global log hook for collecting log entries as dictionaries.
- Injecting simulation time from the global `Simulation` singleton.
- A custom `HookHandler` for forwarding logs to the configured hook
  (e.g., for GUI display, JSON logging, or remote transport).

Core Components
---------------
- `set_logging_hook`: Sets the global log consumption function.
- `get_simulation_time`: Retrieves the current time from the simulation engine.
- `HookHandler`: A custom log handler that emits enriched log dictionaries
  for further processing.

Used in combination with `SimulationTimeFormatter` and `LoggerCategory`
to support custom logger routing and formatting.
"""

from __future__ import annotations
import logging
import time
from typing import Callable, Optional
from qureed.simulation import Simulation


_global_logging_hook: Optional[Callable] = None


def set_logging_hook(hook: Callable):
    """
    Sets the global logging hook.

    Parameters
    ----------
    hook : Callable
        A function that accepts two arguments:
        - log_dict: dict
        - record: logging.LogRecord

    The hook is triggered whenever a log event is emitted through
    `HookHandler`. This enables centralized collection, e.g., for storing logs
    in a database, pushing to a frontend, or aggregating metrics.
    """
    global _global_logging_hook
    _global_logging_hook = hook


def get_global_hook() -> Optional[Callable]:
    """
    Returns the currently configured global logging hook, if any.

    Returns
    -------
    Optional[Callable]
        The currently set logging hook function or `None` if not set.
    """
    return _global_logging_hook


def get_simulation_time():
    """
    Returns the current simulation time.

    This retrieves the simulation time from the global `Simulation` singleton.

    Returns
    -------
    float or None
        The simulation time (in seconds) if available, else `None`.
    """
    try:
        return float(Simulation._instance.simpy_env.now)
    except Exception:
        return None


class HookHandler(logging.Handler):
    """
    A custom logging handler that emits logs to a global hook as structured
    data.

    This handler converts each log record into a dictionary and sends it to
    the global logging hook set via `set_logging_hook()`.

    Each emitted log dictionary contains:
    - timestamp: Wall-clock time
    - simulation_time: Simulated time (if available)
    - message, level, logger: Core logging metadata
    - Optional device-specific fields (e.g., device name, tensor, figure)

    Notes
    -----
    This handler is useful for streaming logs to GUIs or exporting them
    as structured JSON for post-analysis.

    Examples
    --------
    >>> def my_hook(log_dict, record):
    ...     print(log_dict)
    >>> set_logging_hook(my_hook)
    >>> logger.addHandler(HookHandler())
    """

    def emit(self, record):
        if _global_logging_hook:
            log_dict = {
                "timestamp": time.time(),
                "message": record.getMessage(),
                "level": record.levelname,
                "logger": record.name,
                "simulation_time": getattr(
                    record, "simulation_time", get_simulation_time()
                ),
            }

            for attr in (
                "device_name",
                "device",
                "tensor",
                "figure",
                "figure_name",
                "end",
            ):
                if hasattr(record, attr):
                    log_dict[attr] = getattr(record, attr)

            _global_logging_hook(log_dict, record)
