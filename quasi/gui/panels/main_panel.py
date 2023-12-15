import flet as ft

from quasi.gui.board.board import Board
from quasi.gui.bar.simulation_bar import SimulationBar


class MainPanel(ft.UserControl):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.simulation_bar = SimulationBar()
        self.container = ft.Container(
            top=0,
            left=0,
            right=0,
            bottom=0,
            content=ft.Stack(
                [Board(self.page),
                 self.simulation_bar]
                )
        )

    def build(self) -> ft.Container:
        return self.container
