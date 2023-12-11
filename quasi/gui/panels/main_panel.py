import flet as ft

from quasi.gui.board.board import Board


class MainPanel(ft.UserControl):
    def __init__(self, page: ft.Page , width: float, height:float ):
        super().__init__()
        self.page = page
        self.height = height
        self.width = width 
        self.container = ft.Container(
            width=self.width,
            height=self.height,
            bgcolor="blue",
            content=Board(self.page, self.width,self.height)
        )

    def build(self) -> ft.Container:
        return self.container
    

