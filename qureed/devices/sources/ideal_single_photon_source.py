"""
Ideal Single Photon Source implementation
"""
import numpy as np

from qureed._math.fock.ops import a, adagger
from qureed.devices import (
    GenericDevice,
    coordinate_gui,
    ensure_output_compute,
    wait_input_compute,
)
from qureed.devices.port import Port
from qureed.gui.icons import icon_list
from qureed.signals import GenericBoolSignal, GenericQuantumSignal, GenericSignal
from qureed.simulation import ModeManager


class IdealSinglePhotonSource(GenericDevice):
    """
    Implements Ideal Single Photon Source
    """

    ports = {
        "control": Port(
            label="control",
            direction="input",
            signal=None,
            signal_type=GenericBoolSignal,
            device=None,
        ),
        "output": Port(
            label="output",
            direction="output",
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None,
        ),
    }

    # Gui Configuration
    gui_icon = icon_list.SINGLE_PHOTON_SOURCE
    gui_tags = ["ideal"]
    gui_name = "Ideal Single Photon Source"
    gui_documentation = "ideal_single_photon_source.md"

    power_peak = 0
    power_average = 0

    reference = None

    @ensure_output_compute
    @coordinate_gui
    @wait_input_compute
    def compute_outputs(self, *args, **kwargs):
        mm = ModeManager()
        m_id = mm.create_new_mode()
        AD = adagger(mm.simulation.dimensions)
        A = a(mm.simulation.dimensions)
        mode = mm.get_mode(m_id)

        mode = np.matmul(AD, np.matmul(mode, A))
        mm.modes[m_id] = np.matmul(AD, np.matmul(mode, A))
        self.ports["output"].signal.set_contents(timestamp=0, mode_id=m_id)
        self.ports["output"].signal.set_computed()
