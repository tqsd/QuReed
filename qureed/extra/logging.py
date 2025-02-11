"""
This module implements helpers for logging
"""
import datetime
import time
import logging
from enum import Enum

_global_logging_hook = None

def set_logging_hook(hook: callable) -> None:
    global _global_logging_hook
    _global_logging_hook = hook

class HookHandler(logging.Handler):
    def emit(self, record):
        if _global_logging_hook:
            log_entry = {
                "timestamp": time.time(),
                "message": record.getMessage(),
                "level": record.levelname,
                "logger": record.name
            }
            if hasattr(record, "simulation_time"):
                log_entry["simulation_time"]=record.simulation_time
            if hasattr(record, "device_name"):
                log_entry["device_name"]=record.device_name
            if hasattr(record, "device"):
                log_entry["device"]=record.device

            _global_logging_hook(log_entry, record)

class CustomFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        if datefmt:
            s = datetime.datetime.fromtimestamp(record.created).strftime(datefmt)
        else:
            t = datetime.datetime.fromtimestamp(record.created)
            s = t.strftime("%H:%M:%S") + ".%03d" % (t.microsecond // 1000)
        return s


class Loggers(Enum):
    Signals = " signals  "
    Devices = " devices  "
    Simulation = "simulation"


def get_custom_logger(name: Loggers, level=logging.DEBUG):
    """
    Returns a logger instance with specified name and level.
    """
    # Create a logger
    logger = logging.getLogger(name.value)
    logger.setLevel(level)

    # Check if handlers are already configured for this logger
    if not logger.handlers:
        # Create a console handler
        ch = logging.StreamHandler()
        ch.setLevel(level)

        # Create a formatter and set it for the handler
        formatter = CustomFormatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%H:%M:%S.%f",
        )
        ch.setFormatter(formatter)

        # Add the handler to the logger
        logger.addHandler(ch)

        if _global_logging_hook:
            hook_handler = HookHandler()
            hook_handler.setLevel(level)
            hook_handler.setFormatter(formatter)
            logger.addHandler(hook_handler)

    return logger
