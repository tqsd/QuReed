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
    def __init__(self, page: ft.Page, top: float, left: float, device_class, board):
        super().__init__()
        self.page = page
        self.top = top
        self.left = left
        self.board = board
        self.device_class = device_class
        self.ports_out = None
        self.ports_in = None
        self._compute_ports()
        self._header_height = 10
        self._device_height = self._calculate_height()
        self._device_width = self._calculate_width() 
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
            content=ft.GestureDetector(
                drag_interval=1,
                on_vertical_drag_update=self.handle_device_move,
                mouse_cursor=ft.MouseCursor.GRAB
            )
        )

        self._body_controls = []
        if len(self.ports_in.ports) > 0:
            self._body_controls.append(self.ports_in)
        self._body_controls.append(self.image)
        if len(self.ports_out.ports) > 0:
            self._body_controls.append(self.ports_out)

        self._body = ft.Container(
            height=self._device_height - self._header_height,
            width=self._device_width,
            bgcolor="#3f3e42",
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_AROUND,
                spacing=0,
                controls=self._body_controls
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
            device_cls=self.device_class,
            direction="input")
        self.ports_out = Ports(
            device=self,
            page=self.page,
            device_cls=self.device_class,
            direction="output")

    def _calculate_height(self) -> float:
        """
        Implement Logic to calculate height based on
        the number of ports
        """
        return 50

    def _calculate_width(self) -> float:
        """
        Implement Logic to calculate height based on
        the number of ports
        """
        width = 50
        if len(self.ports_in.ports) > 0:
            width += 10
        if len(self.ports_out.ports) > 0:
            width += 10
        return width

    def build(self) -> ft.Container():
        """
        Builds the actual device
        """
        return self.contents

    def handle_device_move(self, e):
        """
        Handler for moving the device component
        """
        self.top += e.delta_y/2
        self.left += e.delta_x/2
        self.contents.top = self.top
        self.contents.left = self.left
        self.ports_in.move(e.delta_x, e.delta_y)
        self.ports_out.move(e.delta_x, e.delta_y)
        self.contents.update()
        self.board.content.update()
        e.control.update()
