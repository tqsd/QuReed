"""
This module implements a charting
"""

import flet as ft
from flet.plotly_chart import PlotlyChart

from qureed.gui.board.base_device_component import BaseDeviceComponent


class Chart(BaseDeviceComponent):
    """
    Displays the chart
    """

    def __init__(self, chart, *args, **kwargs):
        kwargs["resizable"] = True
        kwargs["label"] = "Plot"
        kwargs["width"] = 500
        kwargs["height"] = 500
        super().__init__(*args, **kwargs)

        chart.update_layout(
            width=self.content_width * 0.8, height=self.content_height * 0.8
        )

        self.set_contents(PlotlyChart(chart, expand=True))
