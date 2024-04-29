"""
This module implements the base
functionality, common for all
devices
"""

import flet as ft

from quasi.gui.board.options import DeviceOptions
from quasi.gui.board.info_bar import InfoBar


class BaseDeviceComponent(ft.UserControl):
    """
    Displays the chart
    """
    def __init__(self,
                 page: ft.Page,
                 top: float,
                 left: float,
                 board,
                 device_instance=None,
                 label="",
                 resizable=False,
                 height=100,
                 width=100,
                 ):
        super().__init__()
        self.top = top
        self.left = left
        self.board = board
        self.label = label
        self.has_chart = False
        self._info_bar = InfoBar()
        self.device_instance = device_instance
        self.resizable = resizable
        self.resize_size = 10
        self.header_height = 15
        self.base_wrapper_height = height
        self.base_wrapper_width = width
        self.content_height = self._compute_content_height()
        self.content_width = self._compute_content_width()

        self.base_processing = ft.Container(
            top=2,
            left=2,
            height=5,
            width=5,
            visible=False,
            content=ft.ProgressRing(
                color="white",
                stroke_width=2
            )
        )

        self.base_header = ft.Container(
            top=0,
            left=0,
            right=0,
            height=self.header_height,
            bgcolor="black",
            content=ft.Stack(
               [
                   self.base_processing,
                   ft.Container(
                       left=8,
                       content=ft.Text(
                           label,
                           size=12,
                           color="white")
                   ),
                   ft.GestureDetector(
                       drag_interval=1,
                       on_vertical_drag_update=self.handle_device_move,
                       on_secondary_tap=self.handle_secondary,
                       mouse_cursor=ft.MouseCursor.GRAB,
                       on_enter=self.on_hover_enter,
                       on_exit=self.on_hover_exit
                   )
               ]
            )
        )

        self.contents = None
        self.content_wrapper = ft.Container(
            top=15,
            bottom=0,
            left=0,
            right=0,
            bgcolor="#3f3e42",
            content=ft.Stack([])
        )

        self.resize_container = ft.Container(
            right=0,
            bottom=0,
            opacity=0.2,
            height=self.resize_size,
            width=self.resize_size,
            visible=self.resizable,
            bgcolor="black",
            content=ft.GestureDetector(
                drag_interval=5,
                on_vertical_drag_update=self.handle_device_resize,
                mouse_cursor=ft.MouseCursor.RESIZE_DOWN_RIGHT
            )
        )

        self.base_wrapper = ft.Container(
            width=self.base_wrapper_width,
            height=self.base_wrapper_height,
            top=self.top,
            left=self.left,
            bgcolor="red",
            content=ft.Stack(
                [self.base_header,
                 self.content_wrapper,
                 self.resize_container]
            )
        )

    def set_contents(self, device_content):
        self.content_wrapper.content.controls.append(
            device_content)


    def build(self):
        return self.base_wrapper

    # GUI Logic
    def _compute_content_height(self) -> float:
        h = self.base_wrapper_height
        return h - self.header_height

    def _compute_content_width(self) -> float:
        return self.base_wrapper_width

    # Handlers
    def handle_device_move(self, e):
        """
        Handling the movement of the device
        """
        self.top += e.delta_y/2
        self.left += e.delta_x/2
        self.base_wrapper.top = self.top
        self.base_wrapper.left = self.left
        if hasattr(self, "ports_in"):
            self.ports_in.move(e.delta_x, e.delta_y)
        if hasattr(self, "ports_out"):
            self.ports_out.move(e.delta_x, e.delta_y)
        self.base_wrapper.update()
        self.board.content.update()
        e.control.update()

    def handle_device_resize(self, e):
        """
        Handling the resizing of the device
        """
        self.base_wrapper.width = max(
            self.base_wrapper.width + e.delta_x,
            50)
        self.base_wrapper.height = max(
            self.base_wrapper.height + e.delta_x,
            50)
        
        self.content_height = self._compute_content_height()
        self.content_width = self._compute_content_height()
        self.base_wrapper.update()

    def on_hover_enter(self, e):
        self._info_bar.notify(self.device_instance.__class__.__name__)

    def on_hover_exit(self, e):
        self._info_bar.notify()
    


    def start_processing(self):
        self.base_processing.visible = True
        self.base_wrapper.update()

    def stop_processing(self):
        self.base_processing.visible = False
        self.base_wrapper.update()

    def handle_secondary(self, e):
        """
        Display options
        """
        do = DeviceOptions(self.top+10, self.left+10,
                           self.device_instance, self)
        self.board.create_menu(do)

    def get_port(self, label:str):
        """
        Returns instance of the port
        """
        p = False
        if hasattr(self, "ports_in"):
            p = self.ports_in.get_port(label)
        if p is False:
            if hasattr(self, "ports_out"):
                p = self.ports_out.get_port(label)
        if p is not False:
            return p[0]
        return p
            
        

