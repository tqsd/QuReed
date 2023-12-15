"""
Implements the optical board visualization
and behvaiours
"""

import flet as ft
import flet.canvas as cv

from quasi.gui.board.device import Device
from quasi.gui.simulation.simulation_wrapper import SimulationWrapper


class Board(ft.UserControl):
    __instance = None

    def __init__(self, page: ft.Page):
        super().__init__()
        self.sim_wrapper = SimulationWrapper()
        self.page = page
        self.group = "device"
        self.offset_x = 0
        self.offset_y = 0
        # Canvas draws connection paths

        self.canvas = cv.Canvas(
            [
            ],
            width=float("inf"),
            expand=True,
        )

        self.canvas_container = ft.Container(
            top=0,
            left=0,
            bgcolor="red",
            content=self.canvas,
            )

        # Content stores all of the devices
        self.content = ft.Stack(
            [],
            top=0,
            left=0,
            width=float("inf"),
            height=float("inf"),
        )
        
        self.board = ft.Stack([
            self.canvas_container,
            ft.GestureDetector(
                drag_interval=1,
                on_vertical_drag_update=self.move_board
            ),
            self.content,
        ])
        self.board_wrapper = ft.Container(
            top=50,
            left=0,
            right=0,
            bottom=0,
            content=ft.DragTarget(
                group="device",
                content=ft.Container(
                    expand=True,
                    bgcolor="#a19bac",#"#27262c",
                    content= self.board),
                on_accept=self.drag_accept
            )
        )
        Board.__instance = self

    @classmethod
    def get_canvas(cls):
        """
        Returns the canvas, to draw
        the connecting lines
        """
        return Board.__instance.canvas

    def move_board(self, e):
        """
        Handles the movement of the board
        """
        self.offset_x += e.delta_x
        self.offset_y += e.delta_y

        self.canvas_container.top = min(
            self.canvas_container.top + e.delta_y,
            0)
        self.canvas_container.left = min(
            self.canvas_container.left + e.delta_x,
            0)
        self.content.top = min(self.content.top + e.delta_y, 0)
        self.content.left = min(self.content.left + e.delta_x, 0)
        self.content.update()
        self.canvas_container.update()

    def drag_accept(self, e: ft.DragUpdateEvent):
        """
        Accepts drag device
        """
        dev = self.page.get_control(e.src_id)
        dev_instance = dev.device_class()

        d = Device(
            page=self.page,
            board=self,
            top=(e.y-self.offset_y)/2,
            left=(e.x-self.offset_x)/2,
            device_instance=dev_instance)
        
        self.content.controls.append(d)
        self.content.update()
        self.sim_wrapper.add_device(dev_instance)
        e.control.update()

    def build(self) -> ft.Container():
        """
        Implements the functionality
        required by flet framework
        """
        return self.board_wrapper
