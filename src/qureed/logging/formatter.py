import logging
from qureed.logging.hook import get_simulation_time
from qureed.logging.loggers import LoggerCategory


class SimulationTimeFormatter(logging.Formatter):
    """
    A custom log formatter that prepends simulation time and applies color
    formatting based on logger category.

    This formatter enhances log output by:
    - Automatically including the current siulation time (as `record.simtime`)
      using the `get_simulation_time()` function.
    - Applis ANSI color codes based on the `LoggerCategory` to visually
      distinguish different types of logs.
    - Falling back to `"?.?????????"` if simulation time is unavailable.

    Attributes:
    -----------
    default_time_format: str
        Format used for real (non-simulation) timestamps if needed

    Methods:
    --------
    format(record)
        Formats a log record by injecting simulation time and applying color
        based on the logger category

    Examples:
    ---------
    >>> formatter = SimulationTimeFormatter(fmt="%(simtime)s | %(message)s")
    >>> handler.setFormatter(formatter)
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Formats a log record by injecting simulation time and applying ANSI
        color based on logger category.

        This method overrides `logging.Formatter.format()` to:
        - Add a `simtime` field to the record based on the current simulation
          time.
        - Determine the logger's category from its name using `LoggerCategory`
          and apply the corresponding ANSI color.
        - Reset terminal color formatting after the log line.


        Arguments:
        ----------
        record: logging.LogRecord
           The log record to format.

        Returns:
        --------
        str
            The formatted log string with simulation time and ANSI coloring.

        Notes:
        ------
        - If `get_simulation_time()` fails, the simulation time is shown as
          `"?.?????????"`.
        - If the logger category cannot determined, no color is applied.
        - The `fmt` string passed to the formatter
          (e.g. "%(simtime)s | %(message)s") must incluge `%(simtime)s` to show
          simulation time.
        """
        # Inject simulation time
        try:
            record.simtime = f"{get_simulation_time():.12f}"
        except Exception:
            record.simtime = "?.?????????"

        # Detect logger color
        try:
            category = LoggerCategory.from_logger_name(record.name)
            color = category.color
        except Exception:
            color = "\x1b[0m"  # fallback no color

        # Format with color
        base = super().format(record)
        return f"{color}{base}\x1b[0m"  # reset at end
