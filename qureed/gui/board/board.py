"""
Implements the optical board visualization
and behvaiours
"""

import flet as ft
import flet.canvas as cv

from qureed.gui.board.device import Device
from qureed.gui.board.variable import VariableComponent
from qureed.gui.panels.device_settings import DeviceSettings
from qureed.gui.simulation.simulation_wrapper import SimulationWrapper


def get_class_from_string(class_path):
    """
    Helper for loading board from a saved file
    """
    parts = class_path.split(".")
    module_path = ".".join(parts[:-1])
    class_name = parts[-1]

    module = __import__(module_path, fromlist=[class_name])
    cls = getattr(module, class_name)
    return cls


class Board(ft.UserControl):
    __instance = None

    def __init__(self, page: ft.Page):
        super().__init__()
        self.sim_wrapper = SimulationWrapper()
        self.page = page
        self.group = "device"
        self.offset_x = 0
        self.offset_y = 0
        self.selected_device = None
        self.menus = []
        self.current_scheme = "No diagram opened"
        # Canvas draws connection paths

        self.canvas = cv.Canvas(
            [],
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

        self.scheme_name = ft.Container(
            top=25, left=205, content=ft.Text(self.current_scheme)
        )

        self.board = ft.Stack(
            [
                self.canvas_container,
                ft.GestureDetector(
                    drag_interval=1,
                    on_vertical_drag_update=self.move_board,
                    on_tap=self.on_click,
                    on_scroll=self.on_scroll,
                ),
                self.content,
                self.scheme_name,
            ]
        )
        self.board_wrapper = ft.Container(
            top=0,
            left=0,
            right=0,
            bottom=0,
            content=ft.DragTarget(
                group="device",
                content=ft.Container(
                    expand=True, bgcolor="#a19bac", content=self.board  # "#27262c",
                ),
                on_accept=self.drag_accept,
            ),
        )
        Board.__instance = self

    @classmethod
    def get_canvas(cls):
        """
        Returns the canvas, to draw
        the connecting lines
        """
        return Board.__instance.canvas

    @classmethod
    def get_board(cls):
        """
        Returns the canvas, to draw
        the connecting lines
        """
        return Board.__instance

    def move_board(self, e):
        """
        Handles the movement of the board
        """

        self.clear_menus()
        self.offset_x += e.delta_x
        self.offset_y += e.delta_y

        self.canvas_container.top = min(self.canvas_container.top + e.delta_y, 0)
        self.canvas_container.left = min(self.canvas_container.left + e.delta_x, 0)
        self.content.top = min(self.content.top + e.delta_y, 0)
        self.content.left = min(self.content.left + e.delta_x, 0)

        self.offset_x = min(self.offset_x, 0)
        self.offset_y = min(self.offset_y, 0)
        self.content.update()
        self.canvas_container.update()

    def drag_accept(self, e: ft.DragUpdateEvent):
        """
        Accepts drag device, based on the
        content of the class, it decides what kind
        of component needs to be placed
        """
        self.clear_menus()
        dev = self.page.get_control(e.src_id)
        dev_instance = dev.device_class()
        if "variable" in dev_instance.gui_tags:
            d = VariableComponent(
                page=self.page,
                board=self,
                top=(e.y - self.offset_y - 75) / 2,
                left=(e.x - self.offset_x) / 2,
                device_instance=dev_instance,
            )
        else:
            d = Device(
                page=self.page,
                board=self,
                top=(e.y - self.offset_y - 75) / 2,
                left=(e.x - self.offset_x) / 2,
                device_instance=dev_instance,
            )

        self.content.controls.append(d)
        self.content.update()
        self.sim_wrapper.add_device(dev_instance)
        e.control.update()

    def load_device(self, dev_class, position, uid, values, name=None):
        dev_class = get_class_from_string(dev_class)
        dev_instance = dev_class(uid=uid, name=name)
        if "variable" in dev_instance.gui_tags:
            d = VariableComponent(
                page=self.page,
                board=self,
                top=(position[1]) / 2,
                left=(position[0]) / 2,
                device_instance=dev_instance,
                values=values,
            )
        else:
            d = Device(
                page=self.page,
                board=self,
                top=(position[1]) / 2,
                left=(position[0]) / 2,
                device_instance=dev_instance,
            )

        self.content.controls.append(d)
        self.content.update()
        self.sim_wrapper.add_device(dev_instance)

    def remove_device(self, device):
        self.content.controls.remove(device)
        if hasattr(device, "ports_in"):
            device.ports_in.disconnect_all()
        if hasattr(device, "ports_out"):
            device.ports_out.disconnect_all()
        self.sim_wrapper.remove_device(device.device_instance)
        self.content.update()
        # Remove connections

    def build(self) -> ft.Container():
        """
        Implements the functionality
        required by flet framework
        """
        return self.board_wrapper

    def create_menu(self, menu):
        self.clear_menus()
        self.menus.append(menu)
        self.content.controls.append(menu.build())
        self.content.update()

    def on_click(self, e):
        self.clear_menus()
        self.handle_device_select()

    def on_scroll(self, e):
        pass

    def clear_menus(self):
        for m in self.menus:
            if m.build() in self.content.controls:
                self.content.controls.remove(m.build())
                m.delete_self()
        self.content.update()
        self.menus = []

    def clear_board(self):
        self.content.controls = []
        self.content.update()
        self.sim_wrapper.clear()
        self.canvas.shapes = []
        self.canvas.update()
        self.canvas_container.update()

    def get_device(self, uuid=None, sim_device=None):
        """
        Returns reference to the GUI device, based on
        UUID or simulation device instance
        """
        if sim_device is not None:
            return [
                x for x in self.content.controls if x.device_instance == sim_device
            ][0]
        elif uuid is not None:
            return [
                x for x in self.content.controls if x.device_instance.ref.uuid == uuid
            ][0]
        else:
            raise Exception("Either uuid or sim_device Must be given")

    def set_new_scheme(self, scheme: str):
        self.selected_device = None
        self.handle_device_select()
        self.current_scheme = scheme
        self.scheme_name.content.value = scheme
        self.scheme_name.update()

    def set_label_location(self, top: float, left: float):
        self.scheme_name.top = top
        self.scheme_name.left = left
        self.scheme_name.update()

    def handle_device_select(self, device=None):
        ds = DeviceSettings.get_instance()
        ds.show_device_settings(device)
        if self.selected_device is not None:
            if not device is self.selected_device:
                self.selected_device.deselect()
        self.selected_device = device
