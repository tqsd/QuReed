from enum import Enum


class LoggerCategory(Enum):
    """
    LoggerCategory

    Enum representing predefined logging categories within the QuReed
    simulation framework. Each category defines a logger namespace and
    an associated ANSI color code for terminal output.

    Categories
    ----------
    - GLOBAL      : General-purpose logs (gray)
    - DEVICES     : Logs emitted from device logic (white)
    - CUSTOM      : User-defined or experiment-specific logs (green)
    - SIMULATION  : Internal simulation engine logs (cyan)
    - ERROR       : Error logs (red)
    - SCHEDULING  : Scheduler and event queue logs (yellow)

    Attributes
    ----------
    logger_name : str
        Full namespace name used by Python's logging module.
    color : str
        ANSI escape code for colorizing terminal output.
    """

    GLOBAL = ("qureed.global", "\x1b[38;5;242m")  # gray
    DEVICES = ("qureed.devices", "\x1b[97m")  # white
    CUSTOM = ("qureed.custom", "\x1b[32m")  # green
    FLOW = ("qureed.flow", "\x1b[36m")  # cyan
    ERROR = ("qureed.error", "\x1b[31m")  # red
    SIGNALS = ("qureed.signals", "\x1b[33m")  # yellow

    def __init__(self, logger_name: str, ansi_color: str):
        """
        Arguments
        ----------
        logger_name : str
            Fully qualified logger name (e.g., "qureed.devices").
        ansi_color : str
            ANSI escape code used for colorizing console logs.
        """
        self.logger_name = logger_name
        self.color = ansi_color

    @classmethod
    def from_logger_name(cls, name: str):
        """
        Maps a logger name to the corresponding LoggerCategory.

        Parameters
        ----------
        name : str
            Full logger name (e.g., "qureed.devices").

        Returns
        -------
        LoggerCategory
            Matching category or `LoggerCategory.GLOBAL` if no match is found.
        """
        for item in cls:
            if item.logger_name == name:
                return item
        return cls.GLOBAL  # fallback
