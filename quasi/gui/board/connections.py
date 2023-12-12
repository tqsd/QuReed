"""
This file implements gui functionality
for handling connections between devices
"""

from typing import List, Tuple

import flet as ft
import flet.canvas as cv


class Connection():
    """
    Implements the connection
    """

    def __init__(self,
                 port_A,
                 port_B
                 ):

        from quasi.gui.board.board import Board
        self.strength = 1
        self.port_A = port_A
        self.port_B = port_B
        self.canvas = Board.get_canvas()
        self.connection = None
        self._start_point = port_A.get_location_on_board()
        self._end_point = port_B.get_location_on_board()
        print(self._start_point)
        print(self._end_point)

    def draw(self):
        """
        Draws the connection
        """
        self.connection = cv.Path(
            [
                cv.Path.MoveTo(
                    self._start_point[0],
                    self._start_point[1]
                ),
                cv.Path.CubicTo(
                    self._start_point[0] + self.strength * (
                        self._end_point[0] - self._start_point[0]),
                    self._start_point[1],
                    self._start_point[0] + (1-self.strength) *
                    (self._end_point[0] - self._start_point[0]),
                    self._end_point[1],
                    self._end_point[0],
                    self._end_point[1]
                ),
            ],
            paint=ft.Paint(
                    stroke_width=3,
                    style=ft.PaintingStyle.STROKE,
                ),
        )
        self.canvas.shapes.append(self.connection)
        self.canvas.update()
