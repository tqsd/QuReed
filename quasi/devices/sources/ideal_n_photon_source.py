"""
Ideal Single Photon Source implementation
"""
import numpy as np

from quasi.devices import (GenericDevice,
                           wait_input_compute,
                           coordinate_gui,
                           log_action,
                           ensure_output_compute)
from quasi.devices.port import Port
from quasi.signals import (GenericSignal,
                           QuantumContentType,
                           GenericBoolSignal,
                           GenericIntSignal,
                           GenericQuantumSignal)

from quasi.gui.icons import icon_list
from quasi.simulation import ModeManager
from quasi.extra import Loggers, get_custom_logger

from quasi._math.fock.ops import adagger, a
from quasi.backend.envelope_backend import EnvelopeBackend

from photon_weave.state.envelope import Envelope
from photon_weave.operation.fock_operation import(
    FockOperation, FockOperationType
)


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
    gui_icon = icon_list.N_PHOTON_SOURCE
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

    def set_photon_num(self, photon_num: int):
        """
        Set the number of photons the source should emit in a pulse
        """
        photon_num_sig = GenericIntSignal()
        photon_num_sig.set_int(photon_num)
        self.register_signal(signal=photon_num_sig, port_label="photon_num")
        photon_num_sig.set_computed()

    @log_action
    def des(self, time):
        n = self.ports["photon_num"].signal.contents
        env = Envelope()
        env.label = n
        op = FockOperation(FockOperationType.Creation, apply_count=n)
        env.apply_operation(op)
        next_device = self.get_next_device("output")
        signal = GenericQuantumSignal()
        signal.set_contents(env)
        if next_device:
            self.simulation.schedule_event(
                time,
                next_device,
                signal
            )
