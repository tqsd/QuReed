import inspect
import os

import flet as ft


class DocumentationTab(ft.UserControl):
    def __init__(self, device_instance):
        super().__init__()
        cls_var = device_instance.__class__.__dict__
        cls_dir = os.path.dirname(inspect.getfile(device_instance.__class__))
        documentation_file = f"{cls_dir}/documentation/{cls_var['gui_documentation']}"
        class_file_path = inspect.getfile(device_instance.__class__)
        with open(class_file_path, "r", encoding="utf-8") as class_file:
            impl_py = class_file.read()
            implementaiton = f"""
            ## Implementation
            ```python
            {impl_py}
            ```
            """

        with open(documentation_file, "r", encoding="utf-8") as mdfile:
            md_text = mdfile.read()

        self.content = ft.Tab(
            text=cls_var["gui_name"],
            content=ft.Stack(
                [
                    ft.Container(
                        top=0,
                        left=0,
                        bottom=0,
                        right=300,
                        bgcolor="white",
                        content=ft.Column(
                            expand=True,
                            scroll=ft.ScrollMode.ALWAYS,
                            controls=[
                                ft.Container(height=20),
                                ft.Container(
                                    padding=20,
                                    content=ft.Markdown(
                                        md_text,
                                        selectable=True,
                                        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                                    ),
                                ),
                                ft.Container(height=20),
                                ft.Container(
                                    padding=20,
                                    content=ft.Markdown(
                                        implementaiton,
                                        selectable=True,
                                        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                                    ),
                                ),
                                ft.Container(height=20),
                            ],
                        ),
                    )
                ]
            ),
        )

    def build(self):
        return self.content
