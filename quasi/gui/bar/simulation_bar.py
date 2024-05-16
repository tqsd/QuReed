import flet as ft

from quasi.gui.icons import icon_list
from quasi.gui.simulation.simulation_wrapper import SimulationWrapper
from quasi.simulation import Simulation


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

        self.dimensions = ft.Container(
            height=25,
            width=100,
            content=ft.Row(
                controls=[
                    ft.Icon(
                        name=ft.icons.ALL_OUT,
                        color="white"),
                    ft.TextField(
                        multiline=False,
                        width=40,
                        filled=False,
                        disabled=False,
                        value=str(Simulation.dimensions),
                        content_padding=0,
                        bgcolor="#2b223b",
                        color="white",
                        border=ft.InputBorder.NONE,
                        input_filter=ft.NumbersOnlyInputFilter(),
                        dense=True,
                        on_change=self.on_dimensions_change
                    ),
                 ]
            )
        )

        self.bar = ft.Container(
            bgcolor="#2b223b",
            top=0,
            left=0,
            right=0,
            height=25,
            content=ft.Row(
                [
                    ft.Container(width=2),
                    self.simulate_button,
                    self.dimensions,
                ],
                vertical_alignment=ft.MainAxisAlignment.CENTER)
            )

    def build(self) -> ft.Dropdown:
        return self.bar

    def on_click_simulate(self, e) -> None:
        self.sim_warpper.execute()


    def on_dimensions_change(self, e):
        Simulation.set_dimensions(int(e.control.value))
