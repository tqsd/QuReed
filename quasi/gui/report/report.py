import flet as ft
import logging

class GuiLogHandler(logging.Handler):
    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super(GuiLogHandler, cls).__new__(cls)
        return cls.__instance

    def __init__(self, output_control=None):
        super().__init__()
        if not hasattr(self, 'initialized'):  # Prevents reinitialization
            self.output_control = output_control
            self.log_buffer = []
            self.ready = False
            self.initialized = True

    def emit(self, record):
        log_entry = self.format(record)
        if self.ready and self.output_control.value is not None:
            self.output_control.value += f"\n{log_entry}"
            self.output_control.update()
        else:
            self.log_buffer.append(log_entry)

    def flush_logs(self):
        print("Log Flush")
        if self.ready and self.log_buffer:
            self.output_control.value = "\n".join(self.log_buffer)
            self.output_control.update()
            self.log_buffer.clear()

    def set_ready(self, ready):
        print(f"Set Ready {ready}")
        self.ready = ready
        if ready:
            self.flush_logs()

class Report(ft.UserControl):
    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super(Report, cls).__new__(cls)
        return cls.__instance

    def __init__(self):
        super().__init__()
        if not hasattr(self, 'initialized'):  # Prevents reinitialization
            self.logs_control = ft.TextField(
                label="Logs",
                expand=1,
                multiline=True,
                text_size=14,
                value="",
                read_only=True)
            self.log_handler = GuiLogHandler(self.logs_control)
            self.initialized = True

    def build(self) -> ft.Container:
        return ft.Container(
            top=15,
            left=0,
            right=0,
            bottom=0,
            bgcolor="#FFFFFF",
            content=self.logs_control
        )

    def on_visible_changed(self, visible):
        print("Visible")
        print(self.logs_control.value)
        self.log_handler.set_ready(visible)
