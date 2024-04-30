"""
This module implements helpers for logging
"""

from enum import Enum
import logging

class Loggers(Enum):
    Signals = "signals"
    Devices = "devices"
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
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)

        # Add the handler to the logger
        logger.addHandler(ch)

    return logger
