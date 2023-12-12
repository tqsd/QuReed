"""
QuaSi Gui program.

This file contains the initialization code for the QuaSi Quantum Simulator.
"""
import logging

import flet as ft

from quasi.gui.panels.main_panel import MainPanel
from quasi.gui.panels.side_panel import SidePanel

#logging.basicConfig(level=logging.DEBUG)


class MenuBar(ft.UserControl):
    """MenuBar."""
    def __init__(self) -> None:
        """Initialize the MenuBar instance."""
        super().__init__()
        self.height = 25

    def build(self) -> ft.Container:
        """Build the MenuBar."""
        return ft.Container(
            top=0,
            left=0,
            right=0,
            content=ft.Row([
                ft.Text("File", color="white"),
                ft.Text("Simulate", color="white"),
                ft.Text("Export", color="white")
            ]),
            height=self.height,
            bgcolor="#1f1c1e"
        )


def main(page: ft.Page):
    """Initialize the QuaSi GUI Program."""
    page.padding = 0
    page.window_height = 800
    page.window_width = 900
    page.window_frameless = False

    menu_bar = MenuBar()
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
