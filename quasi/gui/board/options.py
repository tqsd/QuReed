
import flet as ft
from quasi.gui.panels.documentation_panel import DocumentationTab
from quasi.gui.panels.device_settings import DeviceSettings

class DeviceOptions(ft.UserControl):
    def __init__(self, top, left, device_instance, control_instance):
        super().__init__()
        self.device_instance = device_instance
        self.control_instance = control_instance
        self.width = 125
        self.menu = ft.Container(
            top=top*2,
            left=left*2,
            width=self.width,
            border_radius=5,
            height=90,
            bgcolor=ft.colors.BROWN_400,
            content=ft.Column(
                spacing=0,
                controls=[
                    ft.Container(
                        height=25,
                        width=self.width,
                        content=ft.Text("Documentation", color="white"),
                        on_click=self.open_documentation
                    ),
                    ft.Container(
                        height=25,
                        width=self.width,
                        content=ft.Text("Change Direction", color="white"),
                        on_click=self.change_direction
                    ),
                    ft.Container(
                        height=25,
                        width=self.width,
                        content=ft.Text("Delete", color="white"),
                        on_click=self._remove_self
                    ),
                ]
            ),
            shadow=ft.BoxShadow(
                spread_radius=2,
                blur_radius=10,
                color=ft.colors.BLACK26,
                offset=ft.Offset(4, 4),
                blur_style=ft.ShadowBlurStyle.NORMAL,
            )
        )

    def delete_self(self):
        del self

    def _remove_self(self, *args, **kwargs):
        from quasi.gui.board.board import Board
        self.control_instance.handle_remove()
        ds = DeviceSettings.get_instance()
        b = Board.get_board()
        b.remove_device(self.control_instance)
        b.clear_menus()

    def build(self):
        return self.menu

    def open_documentation(self, e):
        from quasi.gui.panels.main_panel import MainPanel
        mp = MainPanel.get_instance()
        dt = DocumentationTab(self.device_instance)
        mp.new_documentation_tab(dt)
        self._remove_self()

    def change_direction(self, e):
        from quasi.gui.board.board import Board
        self.control_instance.change_direction()
        b = Board.get_board()
        b.clear_menus()
