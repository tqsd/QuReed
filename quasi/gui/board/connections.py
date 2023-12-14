"""
This file implements gui functionality
for handling connections between devices
"""

import flet as ft
import flet.canvas as cv

from quasi.gui.simulation import SimulationWrapper

class Connection():
    """
    Implements the connection
    """

    def __init__(self,
                 port_a,
                 port_b
                 ):
        from quasi.gui.board.board import Board
        self.strength = 1
        self.port_a = port_a
        self.port_b = port_b
        self.canvas = Board.get_canvas()
        self.connection = None
        self._start_point = port_a.get_location_on_board()
        self._end_point = port_b.get_location_on_board()
        self._simulation_create_signal()

    def _simulation_create_signal(self):
        print("Creating signal in the simulation kernel")
        print(type(self.port_a))
        print(dir(self.port_a.device))
        print(self.port_a.device)
        print(self.port_b.device)
        print("SIGNAL CREATED")

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
                cv.Path.LineTo(
                    (self._start_point[0]+self._end_point[0])/2,
                    self._start_point[1]
                ),
                cv.Path.LineTo(
                    (self._start_point[0]+self._end_point[0])/2,
                    self._end_point[1]
                ),
                cv.Path.LineTo(
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

    def redraw(self):
        """
        Removes the connection path and creates a new on
        """
        self.canvas.shapes.remove(self.connection)
        self.draw()

    def move(self, port, delta_x, delta_y):
        """
        Handles the change of the connection
        when any device is moved
        """
        if port == self.port_a:
            self._start_point[0] = self._start_point[0] + delta_x
            self._start_point[1] = self._start_point[1] + delta_y
        if port == self.port_b:
            self._end_point[0] = self._end_point[0] + delta_x
            self._end_point[1] = self._end_point[1] + delta_y
        self.redraw()

    def remove(self):
        """
        Removes the connection, with also deleting itself
        """
        self.port_a.connection = None
        self.port_b.connection = None
        self.port_a.deactivate()
        self.port_b.deactivate()
        
        self.canvas.shapes.remove(self.connection)
        self.canvas.update()
        del self


    def hover(self):
        self.connection.paint = ft.Paint(
            stroke_width=3,
            style=ft.PaintingStyle.STROKE,
            color="red"
        )
        self.canvas.update()

    def hover_end(self):
        self.connection.paint = ft.Paint(
            stroke_width=3,
            style=ft.PaintingStyle.STROKE,
            color="black"
        )
        self.canvas.update()
        
