from qureed.logging.core import setup_logger
from qureed.logging.loggers import LoggerCategory


class DeviceLoggingMixin:

    def __init__(self, *args, **kwargs):
        self._enable_logging = False
        self.loggers = {
                "FLOW": setup_logger(LoggerCategory.FLOW),
                }

    @property
    def logger(self):
        # create it on first use, once properties are already set
        if not hasattr(self, "_logger"):
            self._logger = setup_logger(LoggerCategory.DEVICES)
        return self._logger

    @property
    def logging(self) -> bool:
        return self._enable_logging

    @logging.setter
    def logging(self, logging: bool) -> None:
        self._enable_logging = logging

    def log(self, message, **extra):
        if self._enable_logging:
            self.logger.info(f"{self.name} | {message}", extra=self._log_extra(**extra))

    def log_state(self, message, state, **extra):
        if self._enable_logging:
            self.logger.info(
                message, extra=self._log_extra(tensor=state, **extra)
            )

    def log_plot(self, message, figure, figure_name, **extra):
        if self._enable_logging:
            self.logger.info(
                message,
                extra=self._log_extra(
                    figure=figure, figure_name=figure_name, **extra
                ),
            )

    def _log_extra(self, **overrides):
        return {
            "device_name": self.properties["name"].get("value", self.uid),
            "device": self.__class__.__name__,
            **overrides,
        }
