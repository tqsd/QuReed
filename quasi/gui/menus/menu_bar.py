"""
Implements the menu bar
"""

import flet as ft

from quasi.gui.menus.file_menu import FileMenu
from quasi.gui.menus.edit_menu import EditMenu
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
            ]
        )
        self.menu_items = ft.MenuBar(
            expand=True,
            style=ft.MenuStyle(
                alignment=ft.alignment.top_left,
                mouse_cursor={
                    ft.MaterialState.HOVERED: ft.MouseCursor.WAIT,
                    ft.MaterialState.DEFAULT: ft.MouseCursor.ZOOM_OUT},
                ),
            controls=[
                FileMenu(page),
                EditMenu()
            ])
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
