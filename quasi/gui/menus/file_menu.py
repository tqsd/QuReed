"""
Implements the file menu
"""

import flet as ft

from quasi.gui.functionalities.project_management import Project
from quasi.gui.board.board import Board

class FileMenu(ft.UserControl):
    """
    Implements file menu functionality
    """

    def __init__(self, page) -> None:
        super().__init__()
        print(page)
        self.project = Project()
        self.page = page
        self.save_file_dialog = ft.FilePicker(
            on_result=self.handle_save_as)
        self.open_file_dialog = ft.FilePicker(
            on_result=self.handle_open)
        self.page.overlay.extend([
            self.save_file_dialog,
            self.open_file_dialog
        ])
        
        self.menu = ft.SubmenuButton(
            content=ft.Text("File"),
            controls=[
                ft.MenuItemButton(
                    content=ft.Text("New"),
                ),
                ft.MenuItemButton(
                    content=ft.Text("Open"),
                    leading=ft.Icon(ft.icons.FILE_OPEN),
                    on_click=lambda e: self.open_file_dialog.pick_files(
                        allow_multiple=False)
                ),
                ft.MenuItemButton(
                    content=ft.Text("Save"),
                    leading=ft.Icon(ft.icons.SAVE),
                    on_click=self.handle_save
                ), ft.MenuItemButton(
                    content=ft.Text("Save As"),
                    leading=ft.Icon(ft.icons.SAVE),
                    on_click=lambda e: self.save_file_dialog.get_directory_path()
                )
            ]
        )

    def build(self) -> ft.SubmenuButton:
        return self.menu


    def handle_open(self, e):
        """
        """
        board = Board.get_board()
        board.clear_board()
        print(e.files)
        self.project.load(e.files[0].path)
       

    def handle_save(self, e=None):
        """
        Saves the project
        """
        self.project.save()

    def handle_save_as(self, e):
        """
        Saves at a location
        """
        self.temp_location=e.path
        self.location=ft.TextField()
        self.dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Save As"),
            content=ft.Column(
                controls=[
                    ft.Text(f"{e.path}/"),
                    self.location
                ]
            ),
            actions=[
                ft.TextButton(
                    "Confirm",
                    on_click=self.confirm_dialog),
                ft.TextButton(
                    "Cancel",
                    on_click=self.close_dialog)
            ]
        )
        self.page.dialog = self.dlg
        self.dlg.open = True
        self.page.update()

    def confirm_dialog(self, e):
        # update meta information
        self.project.change_project_name(self.location.value)
        self.project.change_location(self.temp_location)
        self.close_dialog()
        self.handle_save()

    def close_dialog(self, e=None):
        self.dlg.open = False
        self.page.update()

    def handle_file_selection(self, e):
        """
        Called after file selected
        """
