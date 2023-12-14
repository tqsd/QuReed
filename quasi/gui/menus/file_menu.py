"""
Implements the file menu
"""

import flet as ft


class FileMenu(ft.UserControl):
    """
    Implements file menu functionality
    """

    def __init__(self) -> None:
        super().__init__()
        self.menu = ft.Container(
            content=ft.Text("File", color="white"),
            on_click=lambda e: print("Clickable without Ink clicked!"),
        )

    def build(self) -> ft.Dropdown:
        return self.menu
