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
            ]
        )
        self.menu_items = ft.Row(
            [
                ft.Container(
                    on_click=self.on_minimize,
                    content=ft.Icon(
                        name=ft.icons.MINIMIZE,
                        color="white"
                    )
                ),
                ft.Container(
                    on_click=self.on_exit,
                    content=ft.Icon(
                        name=ft.icons.CLOSE,
                        color="white"
                    )
                ),
                ft.Container(width=1),
            ]
        )
        self.container = ft.Container(
            top=0,
            left=0,
            right=0,
            height=self.height,
            bgcolor="#1f1c1e",
            content=ft.GestureDetector(
                drag_interval=10,
                content=ft.Row(
                    [
                        self.window_commands,
                        self.menu_items
                    ],
                    width=self.page.window_width,
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                on_vertical_drag_update=self.move_application_window,
                on_double_tap=self.toggle_full_screen
            )
        )

    def move_application_window(self, e) -> None:
        print("——————————————————")
        print(e.delta_x, e.delta_y)
        print(e.local_x, e.local_y)
        print(e.global_x, e.global_y)
        self.page.window_left = e.global_x
        self.page.window_top = e.global_y
        self.page.update()

    def toggle_full_screen(self, e) -> None:
        self.page.window_full_screen = not self.page.window_full_screen
        self.page.update()
        

    def on_minimize(self, e) -> None:
        self.page.minimized=True
        self.page.update()

    def on_exit(self, e) -> None:
        self.page.window_destroy()

    def on_click_simulate(self, e) -> None:
        self.sim_warpper.execute()

    def build(self) -> ft.Container:
        """Build the MenuBar."""
        return self.container
