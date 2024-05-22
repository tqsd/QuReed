"""
This module implements helpers for logging
"""
from enum import Enum
import logging
import datetime

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
    Signals    = " signals  "
    Devices    = " devices  "
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
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S.%f')
        ch.setFormatter(formatter)

        # Add the handler to the logger
        logger.addHandler(ch)

    return logger
