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
                           GenericIntSignal,
                           GenericQuantumSignal)

from quasi.gui.icons import icon_list
from quasi.simulation import ModeManager

from quasi._math.fock.ops import adagger, a


class IdealNPhotonSource(GenericDevice):
    """
    Implements Ideal Single Photon Source
    """
    ports = {
        "trigger": Port(
            label="trigger",
            direction="input",
            signal=None,
            signal_type=GenericBoolSignal,
            device=None),
        "photon_num": Port(
            label="photon_num",
            direction="input",
            signal=None,
            signal_type=GenericIntSignal,
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
    gui_name = "Ideal N Photon Source"
    gui_documentation = "ideal_n_photon_source.md"

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

        photon_num = self.ports["photon_num"].signal.contents
        for i in range(photon_num):
            mode=np.matmul(AD, np.matmul(mode, A))
        mm.modes[m_id]=mode
        self.ports["output"].signal.set_contents(
            content_type=QuantumContentType.FOCK,
            mode_id=m_id)
        self.ports["output"].signal.set_computed()
