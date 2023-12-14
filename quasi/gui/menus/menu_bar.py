"""
Implements the menu bar
"""

import flet as ft

from quasi.gui.menus.file_menu import FileMenu
from quasi.gui.simulation.simulation_wrapper import SimulationWrapper


class MenuBar(ft.UserControl):
    """MenuBar."""
    def __init__(self, page: ft.Page) -> None:
        """Initialize the MenuBar instance."""
        super().__init__()
        self.height = 25
        self.page = page
        self.sim_warpper = SimulationWrapper()
        self.window_commands = ft.Row(
            [
                ft.Container(width=2),
                FileMenu(),
                ft.Container(
                    content=ft.Text("Simulate", color="white"),
                    on_click=self.on_click_simulate
                )
            ]
        )
        self.menu_items = ft.Row(
            [
                ft.Text("Exit", color="white"),
                ft.Container(width=2),
            ]
        )
        self.container = ft.Container(
            top=0,
            left=0,
            right=0,
            height=self.height,
            bgcolor="#1f1c1e",
            content=ft.Row(
                [
                    self.window_commands,
                    self.menu_items
                ],
                width=self.page.window_width,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            )
        )

    def on_click_simulate(self, e) -> None:
        self.sim_warpper.execute()

    def build(self) -> ft.Container:
        """Build the MenuBar."""
        return self.container
