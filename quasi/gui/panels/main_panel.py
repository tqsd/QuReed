import flet as ft

from quasi.gui.board.board import Board
from quasi.gui.bar.simulation_bar import SimulationBar


class MainPanel(ft.UserControl):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.simulation_bar = SimulationBar()
        self.container=ft.Stack(
            [ft.Container(
                top=25,
                left=0,
                right=0,
                bottom=0,
                bgcolor="#130925",
                content=ft.Tabs(
                    tab_alignment=ft.TabAlignment.START,
                    indicator_color="white",
                    divider_color="black",
                    unselected_label_color="white",
                    indicator_padding=0,
                    indicator_tab_size=5,
                    label_color="blue",
                    tabs=[
                        ft.Tab(
                            text="Board",
                            content=ft.Stack(
                                [
                                    ft.Container(
                                        top=0,
                                        left=0,
                                        right=0,
                                        bottom=0,
                                        content=ft.Stack(
                                            [
                                                Board(self.page),
                                                self.simulation_bar
                                            ]
                                        ))]
                            )
                        ),
                        ft.Tab(
                            text="Report",
                        ),
                        ft.Tab(
                            text="Beam Splitter",
                        )
                    ]
                )
            )
             ]
        )
        
    def build(self) -> ft.Container:
        return self.container

    
