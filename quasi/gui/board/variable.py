
import flet as ft

from .base_device_component import BaseDeviceComponent
from .ports import Ports
from .device import DeviceSimGuiCoordinator


class VariableComponent(BaseDeviceComponent):

    def __init__(self, *args, **kwargs):
        # Simulation Connection Components
        self.device_instance = kwargs["device_instance"]
        if "values" in kwargs:
            self.device_instance.values = kwargs["values"]
        self.sim_gui_coordinator = DeviceSimGuiCoordinator(self)
        self.device_instance.set_coordinator(
            self.sim_gui_coordinator
        )

        # Gui Components
        width = 80
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
        self.device_class = self.device_instance.__class__
        if "float" in self.device_class.gui_tags:
            self.input_filter = ft.InputFilter(
                allow=True,
                regex_string=r"[-+]?([0-9]*[.])?[0-9]+([eE][-+]?\d+)?",
                replacement_string="")

        elif "integer" in self.device_class.gui_tags:
            self.input_filter = ft.NumbersOnlyInputFilter()

        print(kwargs)
        value = kwargs.get("values")
        print(value)
        if value:
            print(value)
            value = kwargs.get("value")
        print(value)
        self.field = ft.TextField(
            height=25,
            width=width-10,
            content_padding=0,
            color="white",
            border_color="#c0bfbc",
            on_change=self.change_var,
            text_align=ft.TextAlign.CENTER,
            input_filter=self.input_filter,
            filled=False,
            disabled=False,
            value = value
        )
        self.field_container = ft.Container(
            content=self.field,
            right=15,
            left=10,
            top=5,
            bottom=7,
        )
        self.set_contents(
            ft.Container(
                top=0,
                left=0,
                right=0,
                bottom=0,
                bgcolor="#3f3e42",
                content=ft.Stack(
                    controls=[self.ports_in,
                              self.field_container,
                              self.ports_out,
                              ],
                    expand=True
                )
            )
        )


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

    def change_var(self, e) -> None:
        print(e.control.value)
        self.device_instance.set_value(e.control.value)
