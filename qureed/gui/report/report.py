import logging

import flet as ft


class GuiLogHandler(logging.Handler):
    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super(GuiLogHandler, cls).__new__(cls)
        return cls.__instance

    def __init__(self, output_control=None):
        super().__init__()
        if not hasattr(self, "initialized"):  # Prevents reinitialization
            self.output_control = output_control
            self.log_buffer = []
            self.new_buffer = []
            self.log_count = 0
            self.ready = False

            self.initialized = True

    def set_output_control(self, output_control):
        self.output_control = output_control

    def emit(self, record):
        log_entry = self.format(record)
        if self.ready and self.output_control is not None:
            self.output_control.logs_control.value += f"\n{log_entry}"
            self.output_control.logs_control.update()
        else:
            self.log_count += 1
            self.log_buffer.append(log_entry)
            self.new_buffer.append(log_entry)

    def flush_logs(self):
        if self.ready and self.output_control is not None and self.log_buffer:
            self.output_control.logs_control.value += "\n" + "\n".join(self.log_buffer)
            self.output_control.logs_control.update()
            self.log_buffer.clear()

    def set_ready(self, ready):
        self.ready = ready
        if ready:
            self.flush_logs()


class Report(ft.UserControl):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Report, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        super().__init__()
        if not hasattr(self, "initialized"):  # Prevents reinitialization
            self.logs_control = ft.TextField(
                label=None,
                expand=1,
                multiline=True,
                text_size=14,
                value="",
                color="#FFFFFF",
                border=ft.InputBorder.NONE,
                content_padding=ft.padding.all(20),
                read_only=True,
            )
            self.log_handler = GuiLogHandler(self.logs_control)
            self.initialized = True

    def build(self) -> ft.Container:
        return ft.Container(
            top=15,
            left=0,
            right=0,
            bottom=0,
            bgcolor="#000000",
            content=self.logs_control,
        )

    def clean_logs(self):
        self.logs_control.value = ""

    def save_logs(self):
        pass

    def on_visible_changed(self, visible):
        self.log_handler.set_output_control(self)
        self.log_handler.set_ready(visible)
