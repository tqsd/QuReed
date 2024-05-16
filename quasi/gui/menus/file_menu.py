"""
Implements the file menu
"""

import flet as ft
import os
import venv
from pathlib import Path
import toml
import platform

from quasi.gui.functionalities.project_management import Project
from quasi.gui.board.board import Board
from quasi.gui.project import ProjectManager
import subprocess


class FileMenu(ft.UserControl):
    """
    Implements file menu functionality
    """

    def __init__(self, page) -> None:
        super().__init__()
        self.project = Project()
        self.page = page
        self.save_file_dialog = ft.FilePicker(on_result=self.handle_save_as)
        self.open_file_dialog = ft.FilePicker(on_result=self.handle_open)
        self.new_project_dialog = ft.FilePicker(on_result=self.handle_new_project)
        self.open_project_dialog = ft.FilePicker(on_result=self.handle_open_project)
        self.page.overlay.extend([
            self.save_file_dialog,
            self.open_file_dialog,
            self.new_project_dialog,
            self.open_project_dialog
        ])

        self.menu = ft.SubmenuButton(
            content=ft.Text("File"),
            controls=[
                ft.MenuItemButton(
                    content=ft.Text("New Project"),
                    leading=ft.Icon(ft.icons.FILE_PRESENT_ROUNDED),
                    on_click=lambda e: self.new_project_dialog.get_directory_path(),
                ),
                ft.MenuItemButton(
                    content=ft.Text("Open Project"),
                    leading=ft.Icon(ft.icons.FILE_PRESENT_ROUNDED),
                    on_click=lambda e: self.open_project_dialog.get_directory_path(),
                ),
                ft.MenuItemButton(
                    content=ft.Text("Open"),
                    leading=ft.Icon(ft.icons.FILE_OPEN),
                    on_click=lambda e: self.open_file_dialog.pick_files(
                        allow_multiple=False
                    ),
                ),
                ft.MenuItemButton(
                    content=ft.Text("Save"),
                    leading=ft.Icon(ft.icons.SAVE),
                    on_click=self.handle_save,
                ),
                ft.MenuItemButton(
                    content=ft.Text("Save As"),
                    leading=ft.Icon(ft.icons.SAVE),
                    on_click=lambda e: self.save_file_dialog.get_directory_path(),
                ),
            ],
        )

    def build(self) -> ft.SubmenuButton:
        return self.menu

    def handle_new_project(self, e):
        project_path = e.path
        self.new_project_name = ft.TextField()
        self.dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Save As"),
            content=ft.Column(controls=[ft.Text(f"{e.path}/"), self.new_project_name]),
            actions=[
                ft.TextButton(
                    "Confirm",
                    on_click=lambda e: self.confirm_new_project(e, project_path),
                ),
                ft.TextButton("Cancel", on_click=self.close_dialog),
            ],
        )
        self.page.dialog = self.dlg
        self.dlg.open = True
        self.page.update()

    def confirm_new_project(self, e, project_path):
        project_path = f"{project_path}/{self.new_project_name.value}"
        directories = [
            f"{project_path}/custom/devices",
            f"{project_path}/custom/signals",
            f"{project_path}/logs",
            f"{project_path}/plots",
        ]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)

        # Create files with initial content or empty
        with open(f"{project_path}/experiment.json", "w") as file:
            file.write("{}")  # Empty JSON object as placeholder

        with open(f"{project_path}/config.toml", "w") as file:
            file.write('software = "QuaSi"\n')# TOML configuration for packages
            file.write("packages = []")  # TOML configuration for packages

        python_command = "python3" if platform.system() != "Windows" else "python"

        subprocess.run([python_command, "-m", "venv",  os.path.join(project_path, ".venv")], check=True)
        print([python_command, "-m", "venv",  os.path.join(project_path, ".venv")])
        pm = ProjectManager()
        print("Configuring path")
        pm.configure(path=project_path)
        print("Configuring venv")
        pm.configure(venv=f"{project_path}/.venv")
        print("Installing")
        pm.install("git+ssh://git@github.com/tqsd/QuaSi.git@master")
        self.close_dialog()

    def handle_open_project(self, e):
        project_path = e.path
        config_path = Path(f"{project_path}/config.toml")
        if config_path.exists():
            config_data = toml.load(f"{project_path}/config.toml")
            if not config_data.get("software") == "QuaSi":
                return 
        pm = ProjectManager()
        print("Opening existing project")
        pm.open_project(project_path)

    def handle_open(self, e):
        """ """
        board = Board.get_board()
        board.clear_board()
        self.project.load(e.files[0].path)

    def handle_save(self, e=None):
        """
        Saves the project
        """
        pm = ProjectManager()
        pm.save()

    def handle_save_as(self, e):
        """
        Saves at a location
        """
        self.temp_location = e.path
        self.location = ft.TextField()
        self.dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Save As"),
            content=ft.Column(controls=[ft.Text(f"{e.path}/"), self.location]),
            actions=[
                ft.TextButton("Confirm", on_click=self.confirm_dialog),
                ft.TextButton("Cancel", on_click=self.close_dialog),
            ],
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
        print("close dialog")
        self.dlg.open = False
        self.page.update()

    def handle_file_selection(self, e):
        """
        Called after file selected
        """
