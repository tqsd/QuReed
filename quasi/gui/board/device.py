"""
This file implements gui functionality for the
device component
"""
import flet as ft
import sys
import os

from .ports import Ports
from .chart import Chart
from .base_device_component import BaseDeviceComponent

class Device(BaseDeviceComponent):
    """
    Device class, handles the device gui visualiztaion and
    control
    """
    def __init__(self, *args, **kwargs):

        # Simulation Connection Components
        self.device_instance = kwargs["device_instance"]
        self.sim_gui_coordinator = DeviceSimGuiCoordinator(self)
        self.device_instance.set_coordinator(
            self.sim_gui_coordinator
        )

        # Gui Components
        width = 50
        self.ports_out = None
        self.ports_in = None
        self.page = kwargs["page"]

        self._compute_ports()
        self._ports_width = 10
        self._body_controls = []
        if len(self.ports_in.ports) > 0:
            width += 10
        if len(self.ports_out.ports) > 0:
            width += 10

        super().__init__(
            height=50,
            width=width,
            *args,
            **kwargs)
        # Compute the full path for the image
        if getattr(sys, 'frozen', False):
            # If the application is frozen (packaged by PyInstaller)
            base_path = sys._MEIPASS
            base_path = os.path.join(base_path, 'quasi', 'gui', 'assets')
        else:
            # If running in a normal Python environment
            base_path = os.path.dirname(os.path.abspath(__file__))
            # Correct path to reach the assets directory
            base_path = os.path.join(base_path, '..', 'assets')  # Go up one level and into assets

        full_image_path = os.path.join(base_path, self.device_instance.gui_icon)
        print("Attempting to load image from:", full_image_path)

        self.image = ft.Image(
            src=full_image_path,
            width=self.content_width - 2 * self._ports_width,
            height=self.content_height - self.header_height
        )

        self.image_left = 0
        self.image_right = 0
        if len(self.ports_in.ports) > 0:
            self.image_left = 10
        if len(self.ports_out.ports) > 0:
            self.image_right = 10


        self.set_contents(
            ft.Container(
                top=0,
                left=0,
                right=0,
                bottom=0,
                bgcolor="#3f3e42",
                content=ft.Stack(
                    controls=[self.ports_in,
                              self.ports_out,
                              ft.Container(
                                  top=0,
                                  left=self.image_left,
                                  right=self.image_right,
                                  bottom=0,
                                  content=self.image
                              )
                              ],
                    expand=True
                )
            )
        )

        self.has_chart = False
        if "chart" in self.device_instance.gui_tags:
            self.has_chart = True



    def _compute_ports(self) -> None:
        """
        Create the port component
        """
        self.ports_in = Ports(
            device=self,
            page=self.page,
            device_cls=self.device_instance,
            direction="input")
        self.ports_out = Ports(
            device=self,
            page=self.page,
            device_cls=self.device_instance,
            direction="output")


    def display_chart(self,chart):
        self.board.content.controls.append(
            Chart(
                chart=chart,
                page=self.page,
                top=self.top,
                left=self.left,
                board=self.board))
        self.board.content.update()
        self.page.update()

class DeviceSimGuiCoordinator():
    """
    Manages the coordination between the
    simulated device and the display device
    """

    def __init__(self, gui_device: Device):
        self.device = gui_device
        self.has_chart = False
        self.chart = None
    
    def start_processing(self):
        self.device.start_processing()

    def processing_finished(self):
        self.device.stop_processing()
        if self.device.has_chart and self.has_chart:
            self.device.display_chart(self.chart)


    def set_chart(self, chart):
        self.has_chart = True
        self.chart = chart
