import flet as ft


class DocumentationTab(ft.UserControl):
    def __init__(self, device):
        super().__init__()

        self.content = ft.Markdown("*test")


    def build(self):
        return self.content
        
