"""
This file implements info bar.
Info bar sits at the bottom of the
board, gives more information about various
objects
"""

import flet as ft


class InfoBar(ft.UserControl):
    """
    InfoBar implementation,
    is a singleton
    """

    __instance = None
    __initialized = False

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super(InfoBar, cls).__new__(cls)
        return cls.__instance

    def __init__(self):
        if not self.__initialized:
            super().__init__()
            self.__initialized = True
            self.__modified = False

            self.information = ft.Text("", color="white")
            self.is_saved = ft.Container(
                content=ft.Icon(
                    name=ft.icons.DATA_SAVER_OFF,
                    color=ft.colors.RED,
                    size=15,
                )
            )

            self.row = ft.Row([ft.Container(width=2), self.is_saved, self.information])

            self.bar = ft.Container(
                bottom=0, right=0, left=0, height=20, bgcolor="black", content=self.row
            )

    def set_page(self, page):
        self.__page = page

    def build(self):
        return self.bar

    def notify(self, info=None):
        """
        Notifies the info bar, that some
        information should be displayed
        """
        if info is None:
            self.information.value = ""
            self.notify_save()
        else:
            self.notify_modification()
            self.information.value = info
        self.information.update()
        self.update()

    def notify_save(self) -> None:
        """
        Informs the user that the current project
        is saved
        """
        self.is_saved.name = ft.icons.CHECK_CIRCLE
        self.__modified = False
        self.is_saved.update()
        self.update()

    def notify_modification(self) -> None:
        """
        Informs the user that the changes are
        not saved.
        """
        if not self.__modified:
            self.__modified = True
            self.is_saved.name = ft.icons.DATA_SAVER_OFF
            self.is_saved.update()
