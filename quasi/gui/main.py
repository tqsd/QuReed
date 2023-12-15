"""
QuaSi Gui program.

This file contains the initialization code for the QuaSi Quantum Simulator.
"""
import logging

import flet as ft

from quasi.gui.panels.main_panel import MainPanel
from quasi.gui.panels.side_panel import SidePanel
from quasi.gui.menus.menu_bar import MenuBar
from quasi.gui.bar.simulation_bar import SimulationBar

#logging.basicConfig(level=logging.DEBUG)




def main(page: ft.Page):
    """Initialize the QuaSi GUI Program."""
    page.padding = 0
    page.window_height = 800
    page.window_width = 900
    page.window_frameless = True

    menu_bar = MenuBar(page)
    side_panel = SidePanel(offset_top=menu_bar.height)
    main_panel = MainPanel(page)

    container = ft.Container(
        expand=True,
        content=ft.Stack(
              [
                  main_panel,
                  side_panel,
                  menu_bar,
              ]
        )
    )

    page.add(container)


if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")
