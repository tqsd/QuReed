"""
 created with template
"""
import mpmath
from typing import Union
from qureed.devices import (
    GenericDevice,
    wait_input_compute,
    schedule_next_event,
    coordinate_gui,
    log_action,
    ensure_output_compute,
)
from qureed.devices.port import Port
from qureed.simulation import ModeManager
from qureed.signals import *
from photon_weave.state.envelope import Envelope
from photon_weave.state.composite_envelope import CompositeEnvelope
from photon_weave.operation.polarization_operations import (
    PolarizationOperation,
    PolarizationOperationType,
)
from photon_weave.operation.fock_operation import FockOperationType, FockOperation
from photon_weave.operation.composite_operation import (
    CompositeOperation,
    CompositeOperationType,
)


class EntangledPhotonSource(GenericDevice):
    ports = {
        "trigger": Port(
            label="trigger",
            direction="input",
            signal=None,
            signal_type=GenericBoolSignal,
            device=None,
        ),
        "output": Port(
            label="output",
            direction="output",  # Changed from "input" to "output" for clarity
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None,
        ),
    }

    gui_icon = None
    gui_tags = None
    gui_documentation = None

    power_peak = 0
    power_average = 0

    reference = None

    @ensure_output_compute
    @coordinate_gui
    @wait_input_compute
    def compute_outputs(self, *args, **kwargs):
        """
        Implement to use the regular backend
        """
        pass

    @log_action
    @schedule_next_event
    def des(self, time, *args, **kwargs):
        """
        Implement to use discrete event simulation
        """
        # biexciton
        env1 = Envelope(wavelength=830)
        # exciton
        env2 = Envelope(wavelength=820)
        # Modify Value
        photon_num = 5
        a_dagger = FockOperation(FockOperationType.Creation, apply_count=photon_num)

        env1.apply_operation(a_dagger)
        env2.apply_operation(a_dagger)

        H = PolarizationOperation(operation=PolarizationOperationType.H)
        env1.apply_operation(H)
        CNOT = CompositeOperation(CompositeOperationType.CNOT)
        c = CompositeEnvelope(env1, env2)
        c.apply_operation(CNOT, env1, env2)
        # Time after the biexciton decays
        t1 = mpmath.mpf("0.0000000000001")
        t2 = mpmath.mpf("0.0000000000002")
        s1 = GenericQuantumSignal()
        s1.set_contents(content=env1)
        s2 = GenericQuantumSignal()
        s2.set_contents(content=env2)
        return [("output", s1, time + t1), ("output", s2, time + t2)]

    @log_action
    @schedule_next_event
    def des_action(self, time=None, *args, **kwargs):
        """
        Or implement this if you are implementing a trigger
        """
        pass
