from pathlib import Path

import flet as ft

from quasi.gui.project import ProjectManager
from quasi.gui.panels.side_panel import DraggableDevice

class ProjectPanel(ft.Container):
    _instance = None
    def __init__(self, page):
        super().__init__()
        self.page = page
        self.top = 0
        self.left = 0
        self.bottom = 0
        self.width = 200
        #self.bgcolor = ft.colors.ORANGE_300
        self.bgcolor = "#0b031a"
        self.color = "white"
        self.file_list = ft.Column(
            expand=1,
            spacing=0,
            auto_scroll=True
        )
        self.content = ft.Stack([
            ft.Container(
                top=0,
                right=0,
                bottom=0,
                width=5,
                bgcolor=ft.colors.BLACK,
                on_click=self.toggle_panel,
                content=self.file_list
            ),
            ft.Container(
                top=30,
                right=5,
                bottom=0,
                left=5,
                content=self.file_list
            )
        ])
        pm = ProjectManager()
        self.files = pm.get_file_tree()
        ProjectPanel._instance = self

    def toggle_panel(self, e):
        if self.width == 200:
            self.width = 5
            self.file_list.visible = False
        else:
            self.width = 200
            self.file_list.visible = True

        self.update()

    @staticmethod
    def get_instance():
        return ProjectPanel._instance

    def update_project(self, project_path):
        self.path = project_path
        self.update_file_tree()

    def update_file_tree(self):
        pm = ProjectManager()
        self.files = pm.get_file_tree()

        def recursive_tree_update(files):
            elements = []
            for f in files:
                if isinstance(f, str):
                    elements.append(File(path=f))
                elif isinstance(f, dict):
                    for dir_path, contents in f.items():
                        dir_elements = recursive_tree_update(contents)
                        elements.append(Directory(path=dir_path, elements=dir_elements))
            return elements

        self.file_list.controls = recursive_tree_update(self.files)
        self.file_list.update()
        self.page.update()


class Directory(ft.Column):
    def __init__(self, path, elements):
        self.path = path
        self.name = Path(path).name
        super().__init__()
        self.is_visible = False
        self.spacing = 0
        self.elements = ft.Container(
            padding=0,
            margin=ft.margin.only(left=10),
            content=ft.Column(
                visible=False,
                controls=elements,
                spacing=0
            ))
        self.button = ft.TextButton(
            content=ft.Row([
                ft.Icon(name=ft.icons.KEYBOARD_ARROW_RIGHT),
                ft.Text(
                    self.name,
                    size=15,
                    color="#9d9ca0",
                    weight=ft.FontWeight.BOLD)],
                           spacing=2,
                           ),
            on_click=self.toggle_visibility
        )
        self.controls = [
            self.button,
            self.elements]


    def toggle_visibility(self, e):
        self.elements.content.visible = not self.elements.content.visible
        if self.elements.content.visible:
            self.button.content.controls[0].name=ft.icons.KEYBOARD_ARROW_DOWN
        else:
            self.button.content.controls[0].name=ft.icons.KEYBOARD_ARROW_RIGHT

        self.update()
        e.control.page.update() 

class File(ft.TextButton):
    def  __init__(self, path):
        self.path = path
        self.name = Path(path).name
        super().__init__()


        if self.name[-3:] == ".py":
            pm = ProjectManager()
            self.cls = pm.load_class_from_file(self.path)
            self.content=DraggableDevice(
                d_cls={"class":self.cls},
                group="device",
                content_feedback=ft.Container(
                    width=70,
                    height=50,
                    bgcolor="black",
                    opacity=0.2,
                ),
                content=ft.Text(
                    self.name,
                    size=15,
                    weight=ft.FontWeight.BOLD,
                    color="#9d9ca0")
                )
        else:
            self.content = ft.Text(
                    self.name,
                    size=15,
                    weight=ft.FontWeight.BOLD,
                    color="#9d9ca0")
        self.on_click = self.handle_on_click

    def handle_on_click(self, e):
        if self.name[-5:] == ".json":
            pm = ProjectManager()
            pm.open_scheme(self.name)
