"""
qureed Gui program.

This file contains the initialization code for the qureed Quantum Simulator.
"""

import logging
import os
import sys

import flet as ft

from qureed.gui.menus.menu_bar import MenuBar
from qureed.gui.panels.main_panel import MainPanel
from qureed.gui.panels.project_panel import ProjectPanel
from qureed.gui.panels.side_panel import SidePanel

#  logging.basicConfig(level=logging.DEBUG)


def main(page: ft.Page):
    """Initialize the qureed GUI Program."""

    page.padding = 0
    page.window_height = 800
    page.window_width = 900
    page.window_frameless = False

    menu_bar = MenuBar(page)
    side_panel = SidePanel(offset_top=menu_bar.height)
    main_panel = MainPanel(page)

    container = ft.Container(
        expand=True,
        content=ft.Stack(
            [
                main_panel,
                # side_panel,
                menu_bar,
            ]
        ),
    )
    page.add(container)


def start():
    if getattr(sys, "frozen", False):
        # Running in a bundle
        base_path = sys._MEIPASS
    else:
        # Running in a normal Python environment
        base_path = os.path.dirname(os.path.abspath(__file__))

    assets_path = os.path.join(base_path, "qureed", "gui", "assets")
    ft.app(target=main, assets_dir=assets_path)


if __name__ == "__main__":
    start()
