"""
Implements the Edit menu
"""

import flet as ft


class EditMenu(ft.UserControl):
    """
    Implements file menu functionality
    """

    def __init__(self) -> None:
        super().__init__()
        self.menu = ft.SubmenuButton(
            content=ft.Text("Edit"),
            controls=[
                ft.MenuItemButton(
                    content=ft.Text("Undo"),
                ),
                ft.MenuItemButton(
                    content=ft.Text("Redo"),
                ),
                ft.MenuItemButton(
                    content=ft.Text("Preferences"),
                    leading=ft.Icon(ft.icons.SETTINGS),
                )
            ]
        )

    def build(self) -> ft.SubmenuButton:
        return self.menu


    def handle_save(self, e):
        """
        Saves the project
        """
        print(e)
        print("Save")

    def handle_save_as(self, e):
        """
        Saves at a location
        """
        print("test")
