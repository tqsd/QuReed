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

    mb = MenuBar()
    side_panel = SidePanel(300, page.window_height-mb.height)
    main_panel = MainPanel(page,
                           page.window_width-side_panel.width,
                           page.window_height-mb.height)
    column = ft.Column(
        [
          mb,
          ft.Row(
              [main_panel, side_panel],
              spacing=0,
          )
        ],
        spacing=0,
        height=page.window_height-mb.height,
        width=page.window_width

    )

    page.add(column)


if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")
