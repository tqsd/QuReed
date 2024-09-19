"""
Ideal Coherent Source Implementation
"""
from math import factorial

import numpy as np

from qureed._math.fock.ops import a, adagger, coherent_state
from qureed.devices import (
    GenericDevice,
    coordinate_gui,
    ensure_output_compute,
    wait_input_compute,
)
from qureed.devices.port import Port
from qureed.gui.icons import icon_list
from qureed.signals import (
    GenericBoolSignal,
    GenericFloatSignal,
    GenericQuantumSignal,
    GenericSignal,
)
from qureed.simulation import ModeManager, Simulation


class IdealSqueezedPhotonSource(GenericDevice):
    """
    COHERENT
    """

    ports = {
        "control": Port(
            label="control",
            direction="input",
            signal=None,
            signal_type=GenericBoolSignal,
            device=None,
        ),
        "squeezing": Port(
            label="squeezing",
            direction="input",
            signal=None,
            signal_type=GenericFloatSignal,
            device=None,
        ),
        "offset": Port(
            label="offset",
            direction="input",
            signal=None,
            signal_type=GenericFloatSignal,
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
    gui_icon = icon_list.SQUEEZED_PHOTON_SOURCE
    gui_tags = ["ideal"]
    gui_name = "Ideal Squeezed Photon Source"
    gui_documentation = "ideal_coherent_photon_source.md"

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
        density_matrix = np.zeros(
            (mm.simulation.dimensions, mm.simulation.dimensions), dtype=np.complex128
        )
        alpha = 10

        for m in range(mm.simulation.dimensions):
            for n in range(mm.simulation.dimensions):
                density_matrix[m, n] = (alpha**m * np.conj(alpha) ** n) / np.sqrt(
                    factorial(m) * factorial(n)
                )

        density_matrix /= np.pi

        mm.modes[m_id] = density_matrix
        print(mm.modes[m_id])

        self.ports["output"].signal.set_contents(
            content_type=QuantumContentType.FOCK, mode_id=m_id
        )
        self.ports["output"].signal.set_computed()
