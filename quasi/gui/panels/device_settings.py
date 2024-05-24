
import flet as ft


class DeviceSettings(ft.Container):
    _instance = None

    def __init__(self):
        super().__init__()
        DeviceSettings._instance = self
        self.bottom = 0
        self.right = 5
        self.left = 0
        self.height = 300
        self.visible = False
        self.border = ft.border.only(
            top=ft.border.BorderSide(3, "#fff38e")
        )
        self.content = ft.Column([
        ])

    @staticmethod
    def get_instance():
        return DeviceSettings._instance


    def show_device_settings(self, device=None):
        if device:
            self.visible = True
            self.device = device.device_instance
            self.content.controls = [
                ft.Container(height=5)
            ]
            self.content.controls.extend([
                DeviceSetting(
                    "Name",
                    value=self.device.name,
                    action=lambda prop: self.change_property("name", prop)),
            ])
        else:
            self.device = None
            self.visible = False
        self.update()

    def change_property(self, prop, value):
        setattr(self.device, prop, value)

class DeviceSetting(ft.Row):
    def __init__(self, label, value, action):
        super().__init__()
        self.action= action
        self.controls = [
            ft.TextField(
                label=label,
                color="white",
                width=195,
                height=40,
                value=value,
                on_change=lambda e: self.on_change(e)
            )
        ]

    def on_change(self, e):
        self.action(e.control.value)
        
