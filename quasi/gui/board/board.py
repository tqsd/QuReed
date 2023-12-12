import flet as ft
import flet.canvas as cv
import math
from quasi.gui.board.device import Device


class AlignControl():
    pass



class Board(ft.UserControl):
    __instance = None
    def __init__(self, page: ft.Page):
        super().__init__()
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
        self.devices = []
        self.board_wrapper = ft.DragTarget(
            group="device",
            content=ft.Container(
                expand=True,
                bgcolor="#27262c",
                content= self.board),
            on_accept=self.drag_accept
        )
        print(self.board_wrapper)
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
        print(dir(self.content))
        print(self.content.top)
        self.canvas_container.top = self.canvas_container.top + e.delta_y
        self.canvas_container.left = self.canvas_container.left + e.delta_x

        self.content.top = self.content.top + e.delta_y
        self.content.left = self.content.left + e.delta_x
        self.offset_x += e.delta_x
        self.offset_y += e.delta_y
        self.content.update()
        self.canvas_container.update()

    def drag_accept(self, e: ft.DragUpdateEvent):
        """
        Accepts drag device
        """
        dev = self.page.get_control(e.src_id)
        d = Device(
            page=self.page,
            top=(e.y-self.offset_y)/2,
            left=(e.x-self.offset_x)/2,
            device_class=dev.device_class)


        self.content.controls.append(d)
        self.devices.append(d)
        self.content.update()
        e.control.update()


    def build(self) -> ft.Container():
        return self.board_wrapper
