"""
Side Panel.

Includes the device library
"""

from types import ModuleType
from typing import Any, Dict, List

import flet as ft

import qureed.devices.beam_splitters as qureed_beam_splitters
import qureed.devices.control as qureed_control
import qureed.devices.detectors as qureed_detectors
import qureed.devices.extra as qureed_extra
import qureed.devices.fiber as qureed_fiber
import qureed.devices.investigation_devices as qureed_investigation
import qureed.devices.phase_shifters as qureed_phase_shifters
import qureed.devices.sources as qureed_sources
import qureed.devices.variables as qureed_variables
from qureed.devices import GenericDevice


class DraggableDevice(ft.Draggable):
    """
    Wrapped to carry information to the Board on drag
    """

    def __init__(self, d_cls, group: str, content: ft.Control, content_feedback):
        self.device_class = d_cls["class"]
        super().__init__(
            group=group, content=content, content_feedback=content_feedback
        )


class DeviceItem(ft.UserControl):
    """
    Device Item in the device library.
    """

    def __init__(self, device: GenericDevice):
        super().__init__()
        self.device = device

    def build(self) -> ft.Draggable():
        return DraggableDevice(
            d_cls=self.device,
            group="device",
            content=ft.Row([ft.Text(self.device["name"], size=13, color="white")]),
            content_feedback=ft.Container(
                width=70,
                height=50,
                bgcolor="black",
                opacity=0.2,
            ),
        )


class DeviceList(ft.UserControl):
    """
    Device List
    """

    def __init__(self, width, height):
        super().__init__()
        self.height = height
        self.width = width

    def build(self) -> ft.Container:
        return ft.Container(
            width=self.width, height=self.height, content=self.build_device_list_view()
        )

    def _get_device_class(self, module: ModuleType) -> List[Dict[str, Any]]:
        list_of_devices = [d for d in dir(module) if d[0].isupper() and "_" not in d]
        return_list = []
        for d in list_of_devices:
            device_class = getattr(module, d)
            return_list.append(
                {
                    "name": device_class.gui_name,
                    "icon": device_class.gui_icon,
                    "tags": device_class.gui_tags,
                    "class": device_class,
                }
            )
        return return_list

    def _get_all_devices(self):
        """
        Should get the devices from the
        qureed.devices dir and order them into a dict to be displayed in
        the device library.
        """
        devices_dict = {}
        devices_dict["Variables"] = self._get_device_class(qureed_variables)
        devices_dict["Sources"] = self._get_device_class(qureed_sources)
        devices_dict["Beam Splitters"] = self._get_device_class(qureed_beam_splitters)
        devices_dict["Control"] = self._get_device_class(qureed_control)
        devices_dict["Phase Shift"] = self._get_device_class(qureed_phase_shifters)
        devices_dict["Fiber"] = self._get_device_class(qureed_fiber)
        devices_dict["Detectors"] = self._get_device_class(qureed_detectors)
        devices_dict["Investigation"] = self._get_device_class(qureed_investigation)
        devices_dict["Extra"] = self._get_device_class(qureed_extra)
        return devices_dict

    def build_device_list_view(self) -> ft.ListView():
        """
        Generate the list view of the devices.
        """
        devices = self._get_all_devices()
        lv = ft.ListView()
        for key, value in devices.items():
            d = ft.Text(key, color="white")
            lv_d = ft.ListView(padding=ft.padding.only(left=10))
            for device in value:
                dev = DeviceItem(device)
                lv_d.controls.append(dev)
            lv.controls.append(d)
            lv.controls.append(lv_d)
        return lv


class SidePanel(ft.UserControl):
    """
    Container for the side pannel
    """

    def __init__(self, offset_top: float) -> None:
        super().__init__()
        self.offset_top = offset_top
        self.default_width = 300

    def build(self) -> ft.Container:
        dlist = DeviceList(self.default_width - 5, 800)
        return ft.Container(
            top=self.offset_top,
            bottom=0,
            right=0,
            width=self.default_width,
            bgcolor="#2b223b",
            content=ft.Column(
                [ft.Text("Component Library", color="white", height=25), dlist],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )
