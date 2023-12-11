import flet as ft

class Device(ft.UserControl):
    def __init__(self, top: float, left: float, device_class):
        super().__init__()
        self.top = top
        self.left = left
        self.device_class = device_class
        print(f"Placing device: {top}, {left}")
        print(device_class.gui_icon)
        self.container = ft.Container(
            width=50,
            height=50,
            bgcolor="#3f3e42",
            top=self.top,
            left=self.left,
            content = ft.Column(
                spacing=0,
                controls=[
                    ft.Container(
                        height=10,
                        width=50,
                        bgcolor="black",
                        content=ft.GestureDetector(
                            drag_interval=1,
                            on_vertical_drag_update=self.move
                                                   )),
                    ft.Image(
                        src=self.device_class.gui_icon,
                        width=50,
                        height=40
                    )
                ])
        )

    def build(self) -> ft.Container():
        print(self.container.top)
        print(self.container.left)
        return self.container

    def move(self, e):
        print("MOVING")
        self.top = self.top + e.delta_y
        self.left = self.left + e.delta_x
        self.container.top = self.top
        self.container.left = self.left
        print(self.container.top, self.container.left)
        self.container.update()
        e.control.update()

        
