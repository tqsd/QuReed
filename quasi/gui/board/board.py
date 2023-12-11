import flet as ft


from quasi.gui.board.device import Device


class AlignControl():
    pass



class Board(ft.UserControl):
    def __init__(self, page: ft.Page, width: float, height: float ):
        super().__init__()
        self.height = height
        self.width = width
        self.page = page
        self.group = "device"
        self.content = ft.Stack([
            ft.GestureDetector(
                drag_interval=1,
                on_vertical_drag_update=self.move_board
            )
        ])
        self.devices = []
        self.board = ft.DragTarget(
            group="device",
            content=ft.Container(
                width=self.width,
                height=self.height,
                bgcolor="#27262c",
                content= self.content),
            on_accept=self.drag_accept
        )

    def move_board(self, e):
        for d in self.devices:
            d.container.top = d.container.top + e.delta_y
            d.container.left = d.container.left + e.delta_x
            d.container.update()

    def drag_accept(self, e: ft.DragUpdateEvent):
        dev = self.page.get_control(e.src_id)
        print("DRAG ACCEPT")
        print(type(dev.device_class))
        print(dev.device_class)
        d = Device(top=e.y/2, left=e.x/2,
                   device_class=dev.device_class)
        self.content.controls.append(d)
        self.devices.append(d)

        e.control.update()


    def build(self) -> ft.Container():
        return self.board
