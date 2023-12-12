"""
This file implements gui functionality for the
device component
"""
import flet as ft

from .ports import Ports


class Device(ft.UserControl):
    """
    Device class, handles the device gui visualiztaion and
    control
    """
    # pylint: disable=too-many-instance-attributes
    def __init__(self, page: ft.Page, top: float, left: float, device_class):
        super().__init__()
        self.page = page
        self.top = top
        self.left = left
        print(f"Device Location {self.top}, {self.left}")
        self.device_class = device_class
        self.ports_out = None
        self.ports_in = None
        self._compute_ports()
        self._header_height = 10
        self._device_height = self._calculate_height()
        self._device_width = 70
        self._ports_width = 10

        self.image = ft.Image(
            src=self.device_class.gui_icon,
            width=self._device_width - 2 * self._ports_width,
            height=self._device_height - self._header_height
        )

        self._header = ft.Container(
            height=self._header_height,
            width=self._device_width,
            bgcolor="black",
            on_click=lambda e: print("Clicked somethign"),
            content=ft.GestureDetector(
                drag_interval=1,
                on_vertical_drag_update=self.handle_device_move
            )
        )

        self._body = ft.Container(
            height=self._device_height - self._header_height,
            width=self._device_width,
            bgcolor="#3f3e42",
            content=ft.Row(
                spacing=0,
                controls=[
                    self.ports_in,
                    self.image,
                    self.ports_out
                ]
            )
        )

        self.contents = ft.Container(
            bgcolor=ft.colors.GREEN_200,
            width=self._device_width,
            height=self._device_height,
            top=self.top,
            left=self.left,
            border_radius=2,
            content=ft.Column(
                spacing=0,
                controls=[
                    self._header,
                    self._body]
            )
        )

    def _compute_ports(self) -> None:
        """
        Create the port component
        """
        self.ports_in = Ports(
            device=self,
            page=self.page,
            ports=self.device_class.ports,
            direction="input")
        self.ports_out = Ports(
            device=self,
            page=self.page,
            ports=self.device_class.ports,
            direction="output")

    def _calculate_height(self) -> float:
        """
        Implement Logic to calculate height based on
        the number of ports
        """
        return 50

    def build(self) -> ft.Container():
        print(f"Device returns:{self.contents}")
        return self.contents

    def handle_device_move(self, e):
        """
        Handler for moving the device component
        """
        self.top = self.top + e.delta_y
        self.left = self.left + e.delta_x
        self.contents.top = self.top
        self.contents.left = self.left
        self.contents.update()
        e.control.update()
