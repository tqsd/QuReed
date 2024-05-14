import flet as ft

from quasi.gui.project import ProjectManager

class ProjectPanel(ft.Container):
    _instance = None
    def __init__(self, page):
        super().__init__()
        self.page = page
        self.top = 0
        self.left = 0
        self.bottom = 0
        self.width = 200
        self.bgcolor = ft.colors.ORANGE_300
        self.file_list = ft.Column(
            expand=1,
            spacing=5,
            auto_scroll=True
        )
        self.file_list.contents = ft.Text("test")
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
        print("updating file tree")
        pm = ProjectManager()
        self.files = pm.get_file_tree()

        def recursive_tree_update(files):
            elements = []
            for f in files:
                if isinstance(f, str):
                    print(f"file: {f}")
                    elements.append(File(text=f))
                elif isinstance(f, dict):
                    for dir_name, contents in f.items():
                        dir_elements = recursive_tree_update(contents)
                        elements.append(Directory(name=dir_name, elements=dir_elements))
            return elements

        self.file_list.controls = recursive_tree_update(self.files)
        self.file_list.update()
        self.page.update()


class Directory(ft.Column):
    def __init__(self, name, elements):
        super().__init__()
        self.is_visible = False
        self.elements = ft.Container(
            padding=0,
            margin=ft.margin.only(left=20),
            content=ft.Column(
                visible=False,
                controls=elements
        ))
        self.controls = [
            ft.TextButton(
                name,
                on_click=self.toggle_visibility),
            self.elements]


    def toggle_visibility(self, e):
        self.elements.content.visible = not self.elements.content.visible
        self.update()
        e.control.page.update() 

class File(ft.TextButton):
    def  __init__(self, text):
        super().__init__()
        self.text = text 
        self.on_click = self.handle_on_click

    def handle_on_click(self, e):
        if self.text[-5:] == ".json":
            pm = ProjectManager()
            pm.open_scheme(self.text)

       
    
