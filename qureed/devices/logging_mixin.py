
class DeviceLoggingMixin:
    def log(self, message, **extra):
        self.logger.info(message, extra=self._log_extra(**extra))

    def log_state(self, message, state, **extra):
        self.logger.info(message, extra=self._log_extra(tensor=state, **extra))

    def log_plot(self, message, figure, figure_name, **extra):
        self.logger.info(
            message,
            extra=self._log_extra(figure=figure, figure_name=figure_name, **extra)
        )

    def _log_extra(self, **overrides):
        return {
            "device_name": self.properties["name"].get("value", self.uid),
            "device": self.__class__.__name__,
            **overrides,
        }
