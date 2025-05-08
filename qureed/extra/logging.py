"""
This module implements helpers for logging
"""
import datetime
import time
import logging
from enum import Enum

_global_logging_hook = None
_simulation = None

def set_logging_hook(hook: callable) -> None:
    global _global_logging_hook
    _global_logging_hook = hook

def set_simulation(simulation) -> None:
    global _simulation
    _simulation = simulation

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
            elif _simulation is not None:
                log_entry["simulation_time"]=float(_simulation.current_time)
            if hasattr(record, "device_name"):
                log_entry["device_name"]=record.device_name
            if hasattr(record, "device"):
                log_entry["device"]=record.device
            if hasattr(record, "end"):
                log_entry["end"] = bool(record.end)
            if hasattr(record, "tensor"):
                log_entry["tensor"]=record.tensor
            if hasattr(record, "figure"):
                log_entry["figure"]=record.figure
            if hasattr(record, "figure_name"):
                log_entry["figure_name"]=record.figure_name


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
    Signals = "SIG"
    Devices = "DEV"
    Simulation = "SIM"
    Custom = "CUS"
    Scheduling = "SCH"
    Error = "ERR"

class DeviceLoggingAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        if self.extra:
            kwargs.setdefault("extra", {}).update(self.extra)
        return msg, kwargs


def get_custom_logger(name: Loggers, level=logging.DEBUG, device=None):
    """
    Returns a logger instance with specified name and level.
    """
    # Create a logger
    logger = logging.getLogger(name.value)
    logger.setLevel(level)

    # Check if handlers are already configured for this logger
    if not any(isinstance(h, HookHandler) for h in logger.handlers):
        # Create a console handler

        # Create a formatter and set it for the handler
        formatter = CustomFormatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%H:%M:%S.%f",
        )

        # Add the handler to the logger
        if _global_logging_hook:
            hook_handler = HookHandler()
            hook_handler.setLevel(level)
            hook_handler.setFormatter(formatter)
            logger.addHandler(hook_handler)

    extra = {}
    if device:
        extra["device_name"]=device.properties["name"].get(
            "value", device.uid
        )
        extra["device_type"]=device.__class__.__name__
    return logger
    return DeviceLoggingAdapter(logger, extra)
