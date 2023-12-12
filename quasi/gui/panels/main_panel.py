import flet as ft

from quasi.gui.board.board import Board


class MainPanel(ft.UserControl):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.container = ft.Container(
            top=0,
            left=0,
            right=0,
            bottom=0,
            content=Board(self.page)
        )

    def build(self) -> ft.Container:
        return self.container
