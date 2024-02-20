"""
This file implements
the gui port functionality
"""
from typing import List, Tuple

import flet as ft
import flet.canvas as cv

from quasi.devices.port import Port
from quasi.gui.board.connections import Connection
from quasi.gui.board.info_bar import InfoBar
from quasi.gui.simulation import SimulationWrapper

def get_class_from_string(class_path):
    """
    Helper for loading board from a saved file
    """
    parts = class_path.split('.')
    module_path = '.'.join(parts[:-1])
    class_name = parts[-1]

    module = __import__(module_path, fromlist=[class_name])
    cls = getattr(module, class_name)
    return cls


class PortComponent(ft.UserControl):
    """
    Port represents an individual port
    it includes logic for GUI port.
    """

    def __init__(self,
                 page: ft.Page,
                 index:  int,
                 num_of_ports: int,
                 label,
                 device_comp,
                 device_cls,
                 side: str,
                 port_instance=None):
        super().__init__()
        self.num_of_ports = num_of_ports
        self.index = index
        self.page = page
        self.label = label
        self.device = device_comp
        self.device_cls = device_cls
        self.side = side
        self.port_instance = port_instance
        self.connection = None
        self._info_bar = InfoBar()
        if side == Ports.left_side:
            self.right_radius = 5
            self.left_radius = 0
        else:
            self.right_radius = 0
            self.left_radius = 5
        self.port_comp = ft.GestureDetector(
            on_enter=self.connection_hover_enter,
            on_exit=self.connection_hover_exit,
            on_secondary_tap=self.handle_on_right_click,
            on_tap=self.handle_on_left_click,
            mouse_cursor=ft.MouseCursor.CLICK,
            content=ft.Container(
                height=10,
                width=10,
                bgcolor=Ports.default_color,
                border_radius=ft.border_radius.horizontal(
                    left=self.left_radius,
                    right=self.right_radius)
            )
        )

    def build(self) -> ft.Container:
        return self.port_comp

    def connection_hover_enter(self, e):
        self._info_bar.notify(
            f"{self.label} : {self.port_instance.signal_type.__name__}"
        )
        if self.connection is not None:
            self.connection.hover()

    def connection_hover_exit(self, e):
        self._info_bar.notify()
        if self.connection is not None:
            self.connection.redraw()

    def get_location_on_board(self) -> Tuple[float, float]:
        """
        Get center coordinates of the
        port relative to the
        ft.Stack()
        """
        x = 2*self.device.left
        if self.side == Ports.right_side:
            x += self.device.base_wrapper_width - 5
        elif self.side == Ports.left_side:
            x += 5
        y = 2*self.device.top + self.device.header_height
        y += self.vertical_offset()
        return [x, y]

    def vertical_offset(self) -> float:
        """
        Computes vertical offset of the port component
        """
        offset = (self.device.base_wrapper_height -
                  self.device.header_height)
        offset /= self.num_of_ports * 2
        offset = offset * (1 + 2*self.index)
        return offset

    def connect(self):
        """
        Modifies the port on when connected
        """
        self.port_comp.content.bgcolor = Ports.connected_color
        self.port_comp.content.update()

    def disconnect(self):
        """
        Modifies the port when disconnected
        """
        self.port_comp.content.bgcolor = Ports.default_color
        self.port_comp.content.update()

    def activate(self):
        """
        Modifies the port when activated
        """
        self.port_comp.content.bgcolor = Ports.active_color
        self.port_comp.content.update()

    def deactivate(self):
        """
        Modifies the port when deactivated
        """
        self.port_comp.content.bgcolor = Ports.default_color
        self.port_comp.content.update()

    def handle_on_left_click(self, e):
        """
        Handles functionality when
        the port is clicked
        """
        _ = e
        bc = BoardConnector(self.page)
        bc.handle_connect(self, self.device_cls, self.label)


    def handle_on_right_click(self, e):
        _ = e
        bc = BoardConnector(self.page)
        bc.handle_disconnect(self)

    def assign_connection(self, connection):
        self.connection = connection

    def move(self, delta_x, delta_y):
        """
        Handles the behaviour, when the device
        component is moved on the board
        """
        if self.connection is not None:
            self.connection.move(self, delta_x, delta_y)



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

    def __init__(
            self,
            page: ft.Page,
            device,
            device_cls,
            direction: str = "input"):
        super().__init__()
        self.page = page
        self.device = device
        self.device_cls = device_cls
        self.ports = []
        self.ports_controls = []
        for _, item in device_cls.ports.items():
            if item.direction == direction:
                self.ports.append(item)
        self.left_radius = 0
        self.right_radius = 0
        if direction == "input":
            self.side = Ports.left_side
        elif direction == "output":
            self.side = Ports.right_side
        self.create_ports(self.side)

    def build(self) -> ft.Container():
        return ft.Container(
            top=0,
            bottom=0,
            right=0 if self.side == Ports.right_side else None,
            left=0 if self.side == Ports.left_side else None,
            width=10,
            content=ft.Column(
                spacing=5,
                alignment=ft.MainAxisAlignment.SPACE_AROUND,
                controls=self.ports_controls
            )
        )

    def create_ports(self, side):
        """
        Creates ports component
        """
        for i, port in enumerate(self.ports):
            self.ports_controls.append(
                PortComponent(
                    index=i,
                    num_of_ports=len(self.ports),
                    label=port.label,
                    page=self.page,
                    side=side,
                    device_comp=self.device,
                    device_cls=self.device_cls,
                    port_instance=port
                )
            )

    def move(self, delta_x, delta_y):
        for p in self.ports_controls:
            p.move(delta_x, delta_y)

    def get_port(self, label):
        if label in [p.label for p in self.ports]:
            return [p for p in self.ports_controls if p.label == label]
        else:
            return False


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

    def __init__(self, *args, **kwargs):
        # pylint: disable=import-outside-toplevel
        from quasi.gui.board.board import Board
        if not hasattr(self, 'initialized'):
            self.first_location = None
            self.page = Board.get_board().page
            self.first_click = None
            self.initialized = True  # Mark as initialized
            self.canvas = Board.get_canvas()
            self.board = Board.get_board()

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

    def handle_disconnect(self, port: Port):
        """
        Handles disconnect, when port is clicked
        with right click
        """
        if port.connection is not None:
            port.connection.remove()

    def handle_connect(self, port: Port, device_cls, label):
        """
        Handler for connection creation.
        """
        self.board.clear_menus()
        if port.connection is not None:
            if self.first_click is not None:
                self.first_click.deactivate()
                self.first_click = None
            return
        if self.first_click is None:
            self.first_click = {
                "port": port,
                "device_cls": device_cls,
                "label": label
            }
            self.first_location = port.get_location_on_board()
            self.first_click["port"].activate()
        else:

            # INFORM THE SIMULATION KERNEL ABOUT THE CONNECTION
            sim_wrp = SimulationWrapper()
            # Checking if the signals match
            sig_1_cls = self.first_click["device_cls"].ports[self.first_click["label"]].signal_type
            sig_2_cls = device_cls.ports[label].signal_type
            print(sig_1_cls)
            print(sig_2_cls)
            parent_sig_cls = None
            if issubclass(sig_1_cls, sig_2_cls):
                parent_sig_cls = sig_2_cls
            elif issubclass(sig_2_cls, sig_1_cls):
                parent_sig_cls = sig_1_cls
            else:
                print("PORTS INCOMPATIBLE; CONNECTION NOT POSSIBLE")
                self.first_click = None
                return
            parent_sig_obj = parent_sig_cls()
            sim_wrp.create_connection(
                sig=parent_sig_obj,
                dev1=self.first_click["device_cls"],
                port_label_1=self.first_click["label"],
                dev2=device_cls,
                port_label_2=label
            )
            self.first_click["port"].connect()
            conn = Connection(port_a=self.first_click["port"],
                              port_b=port)
            port.connect()
            conn.draw()
            self.first_click["port"].assign_connection(conn)
            port.assign_connection(conn)
            self.first_click = None

    def load_connection(self, connection):
        from quasi.gui.board.board import Board
        sim_wrp = SimulationWrapper()
        signal_class = get_class_from_string(connection["signal"])
        dev1 = sim_wrp.get_device(connection["conn"][0]["device_uuid"])
        pl1 = connection["conn"][0]["port"]
        dev2 = sim_wrp.get_device(connection["conn"][1]["device_uuid"])
        pl2 = connection["conn"][1]["port"]

        sim_wrp.create_connection(
            sig=signal_class(),
            dev1=dev1,
            port_label_1=pl1,
            dev2=dev2,
            port_label_2=pl2
        )
        b = Board.get_board()
        port1 = b.get_device(sim_device=dev1).get_port(pl1)
        print(port1)
        port2 = b.get_device(sim_device=dev2).get_port(pl2)
        print(port2)

        conn = Connection(port_a=port1, port_b=port2)
        port1.connect()
        port1.assign_connection(conn)
        port2.connect()
        port2.assign_connection(conn)
        conn.draw()
