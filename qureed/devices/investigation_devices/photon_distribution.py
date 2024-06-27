"""
Photon Distribution
"""
import numpy as np
import plotly.express as px

from qureed.devices import (
    GenericDevice,
    coordinate_gui,
    ensure_output_compute,
    wait_input_compute,
)
from qureed.devices.port import Port
from qureed.gui.icons import icon_list
from qureed.signals import GenericQuantumSignal, GenericSignal
from qureed.simulation import ModeManager


class PhotonDistribution(GenericDevice):
    """
    Implements Photon Distribution Grapphing device
    """

    ports = {
        "IN": Port(
            label="IN",
            direction="input",
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None,
        ),
    }

    # Gui Configuration
    gui_icon = icon_list.HISTOGRAM
    gui_tags = ["investigate", "chart"]
    gui_name = "Photon Distribution"

    power_average = 0
    power_peak = 0
    reference = 0

    @wait_input_compute
    @coordinate_gui
    def compute_outputs(self, *args, **kwargs):
        mm = ModeManager()
        m_id = self.ports["IN"].signal.mode_id
        mode = mm.get_mode(m_id)
        probabilities = np.real(np.diag(mode))

        histogram_data = {
            "State": [str(i) for i in range(len(probabilities))],
            "Probability": probabilities,
        }

        # Create a histogram using Plotly Express
        fig = px.bar(
            histogram_data,
            x="State",
            y="Probability",
            labels={"Probability": "Probability Amplitude", "State": "Fock State"},
            title="Fock State Density Matrix Histogram",
        )

        # Show the plot
        # fig.show()
        if hasattr(self, "coordinator"):
            self.coordinator.set_chart(fig)
