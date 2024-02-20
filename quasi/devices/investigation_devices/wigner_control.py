"""
Create wigner distribution plots
"""

import numpy as np
from scipy.linalg import sqrtm
from scipy.fft import fftn, fftfreq
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import plotly.graph_objects as go

from quasi.devices import (GenericDevice,
                           wait_input_compute,
                           coordinate_gui,
                           ensure_output_compute)
from quasi.devices.port import Port
from quasi.signals import (GenericSignal,
                           GenericQuantumSignal)

from quasi.gui.icons import icon_list

from quasi.simulation import ModeManager

from qutip.wigner import wigner
from qutip import Qobj


class WignerControl(GenericDevice):
    """
    Implements Wigner Plot creation device
    """
    ports = {
        "IN": Port(
            label="IN",
            direction="input",
            signal=None,
            signal_type=GenericQuantumSignal, device=None),
    }

    # Gui Configuration
    gui_icon = icon_list.WIGNER_CONTROL
    gui_tags = ["investigate", "chart"]
    gui_name = "Wigner Quasi Probability"

    power_average = 0
    power_peak = 0
    reference = 0

    @wait_input_compute
    @coordinate_gui
    def compute_outputs(self, *args, **kwargs):
        mm = ModeManager()
        m_id = self.ports["IN"].signal.mode_id
        mode = mm.get_mode(m_id)
        # Show the plot


        # Plot Wigner probability
        print(mode)
        xvec = np.linspace(-5,5,200)

        W = wigner(Qobj(mode), xvec, xvec)

        fig = go.Figure()

        fig.add_trace(go.Surface(z=W, x=xvec, y=xvec, colorscale="Viridis"))

        # Set the layout of the figure
        fig.update_layout(
            title="Wigner Function",
            scene=dict(
                xaxis_title="Re(alpha)",
                yaxis_title="Im(alpha)",
                zaxis_title="Wigner Function",
            )
        )

        if hasattr(self, "coordinator"):
            self.coordinator.set_chart(fig)



