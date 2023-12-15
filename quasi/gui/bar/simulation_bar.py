import flet as ft

from quasi.gui.icons import icon_list
from quasi.gui.simulation.simulation_wrapper import SimulationWrapper


class SimulationBar(ft.UserControl):
    """
    Implements file menu functionality
    """

    def __init__(self) -> None:
        super().__init__()

        self.sim_warpper = SimulationWrapper()
        self.simulate_button = ft.Container(
            width=25,
            height=25,
            content=ft.Icon(
                name=ft.icons.PLAY_CIRCLE_OUTLINED,
                color="white"
            ),
            on_click=self.on_click_simulate
        )


        self.bar = ft.Container(
            bgcolor="#2b223b",
            top=25,
            left=0,
            right=0,
            height=25,
            content=ft.Row(
                [
                    ft.Container(width=2),
                    self.simulate_button
                ]
            )
        )

    def build(self) -> ft.Dropdown:
        return self.bar

    def on_click_simulate(self, e) -> None:
        self.sim_warpper.execute()

