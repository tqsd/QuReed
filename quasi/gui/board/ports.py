"""
This file implements
the gui port functionality
"""
from typing import List, Tuple

import flet as ft
import flet.canvas as cv

from quasi.devices.port import Port


class PortComponent(ft.UserControl):
    """
    Port represents an individual port
    it includes logic for GUI port.
    """

    def __init__(self,
                 page: ft.Page,
                 index:  int,
                 num_of_ports: int,
                 device,
                 side: str):
        super().__init__()
        self.num_of_ports = num_of_ports
        self.index = index
        self.page = page
        self.device = device
        self.side = side
        if side == Ports.left_side:
            self.right_radius = 5
            self.left_radius = 0
        else:
            self.right_radius = 0
            self.left_radius = 5
        self.port_comp = ft.Container(
            height=10,
            width=10,
            bgcolor=Ports.default_color,
            on_click=self.handle_on_click,
            border_radius=ft.border_radius.horizontal(
                left=self.left_radius,
                right=self.right_radius)
        )

    def build(self) -> ft.Container:
        return self.port_comp

    def get_location_on_board(self) -> Tuple[float, float]:
        """
        Get center coordinates of the
        port relative to the
        ft.Stack()
        """
        print("GET location on board")
        x = 2*self.device.left
        print(self.side)
        if self.side == Ports.right_side:
            print("RIGHT")
            x += self.device._device_width - 5
        elif self.side == Ports.left_side:
            print("LEFT")
            x += 5
        y = 2*self.device.top + self.device._header_height
        y += self.vertical_offset()
        print(f"Port loctaion {x},{y}")
        return (x, y)

    def vertical_offset(self) -> float:
        """
        Computes vertical offset of the port component
        """
        offset = self.device._device_height - self.device._header_height
        offset /= self.num_of_ports * 2
        offset = offset * (1 + 2*self.index)
        return offset

    def connect(self):
        """
        Modifies the port on when connected
        """
        self.port_comp.bgcolor = Ports.connected_color
        self.port_comp.update()

    def disconnect(self):
        """
        Modifies the port when disconnected
        """
        self.port_comp.bgcolor = Ports.default_color
        self.port_comp.update()

    def activate(self):
        """
        Modifies the port when activated
        """
        self.port_comp.bgcolor = Ports.active_color
        self.port_comp.update()

    def deactivate(self):
        """
        Modifies the port when deactivated
        """
        self.port_comp.bgcolor = Ports.default_color
        self.port_comp.update()

    def handle_on_click(self, e):
        """
        Handles functionality when
        the port is clicked
        """
        _ = e
        bc = BoardConnector(self.page)
        bc.handle_connect(self)


class Ports(ft.UserControl):
    """
    Ports is a component, which includes
    individual ports.
    """

    default_color = "#2d2c2f"
    active_color = "yellow"
    connected_color = "yellow"
    right_side = "RIGHT"
    left_side = "LEFT"

    def __init__(self, page: ft.Page, device,
                 ports: List[Port],
                 direction: str = "input"):
        super().__init__()
        self.page = page
        self.device = device
        self.ports = []
        self.ports_controls = []
        for _, item in ports.items():
            if item.direction == direction:
                self.ports.append(Port)
        self.left_radius = 0
        self.right_radius = 0
        if direction == "input":
            self.side = Ports.left_side
        elif direction == "output":
            self.side = Ports.right_side
        self.create_ports(self.side)

    def build(self) -> ft.Column():
        return ft.Column(
            spacing=5,
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
            controls=self.ports_controls
        )

    def create_ports(self,side):
        """
        Creates ports component
        """
        for i, _  in enumerate(self.ports):
            self.ports_controls.append(
                PortComponent(
                    index=i,
                    num_of_ports=len(self.ports),
                    page=self.page,
                    side=side,
                    device=self.device
                )
            )


class BoardConnector():
    """
    BoardConnector implements
    the port connecting functionality
    This is a singleton class
    """

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'):
            cls.instance = super(BoardConnector, cls).__new__(cls)
        return cls.instance

    def __init__(self, page: ft.Page):
        # pylint: disable=import-outside-toplevel
        from quasi.gui.board.board import Board
        if not hasattr(self, 'initialized'):
            self.first_location = None
            self.page = page
            self.first_click = None
            self.initialized = True  # Mark as initialized
            self.canvas = Board.get_canvas()

    def draw_connection(self, point1=(100, 100),
                        point2=(200, 200)):
        """
        Draws the connection between the
        two points
        """
        strength = 0.8
        conn = cv.Path(
            [
                cv.Path.MoveTo(point1[0], point1[1]),
                cv.Path.CubicTo(
                    point1[0] + strength * (point2[0] - point1[0]),
                    point1[1],
                    point1[0] + (1-strength) * (point2[0] - point1[0]),
                    point2[1],
                    point2[0], point2[1]
                ),
            ],
            paint=ft.Paint(
                    stroke_width=3,
                    style=ft.PaintingStyle.STROKE,
                ),
        )
        self.canvas.shapes.append(conn)
        self.canvas.update()

    def handle_connect(self, port: Port):
        """
        Handler for connection creation.
        """
        if self.first_click is None:
            self.first_click = port
            print("GETTING LOCATION ON BOARD")
            self.first_location = port.get_location_on_board()
            self.first_click.activate()
        else:
            self.first_click.connect()
            port.connect()
            self.draw_connection(
                point1=self.first_location,
                point2=port.get_location_on_board())
            self.first_click = None
