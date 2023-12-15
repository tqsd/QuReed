"""
Ideal Single Photon Source implementation
"""
import numpy as np

from quasi.devices import (GenericDevice,
                           wait_input_compute,
                           coordinate_gui,
                           ensure_output_compute)
from quasi.devices.port import Port
from quasi.signals import (GenericSignal,
                           QuantumContentType,
                           GenericBoolSignal,
                           GenericQuantumSignal)

from quasi.gui.icons import icon_list
from quasi.simulation import ModeManager

from quasi._math.fock.ops import adagger, a


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
            device=None),
        "output": Port(
            label="output",
            direction="output",
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None),
    }

    # Gui Configuration
    gui_icon = icon_list.SINGLE_PHOTON_SOURCE
    gui_tags = ["ideal"]
    gui_name = "Ideal Single Photon Source"

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
        mm.modes[m_id] =  np.matmul(AD, np.matmul(mode, A))
        self.ports["output"].signal.set_contents(
            content_type=QuantumContentType.FOCK,
            mode_id=m_id)
        self.ports["output"].signal.set_computed()

