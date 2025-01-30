"""
Ideal Beam Splitter
"""

import heapq
import mpmath

from qureed.devices.generic_device import (
    GenericDevice,
    log_action,
    schedule_next_event,
)
from qureed.devices.port import Port
from qureed.simulation import Simulation
from qureed.extra import Reference
from qureed.signals import GenericQuantumSignal
from qureed.assets import icon_list

from photon_weave.state.envelope import Envelope
from photon_weave.state.composite_envelope import CompositeEnvelope
from photon_weave.operation import Operation, CompositeOperationType


_BEAM_SPLITTER_BIB = {
    "title": "Quantum theory of the lossless beam splitter",
    "author": "Fearn, H and Loudon, R",
    "journal": "Optics communications",
    "volume": 64,
    "number": 6,
    "pages": "485--490",
    "year": 1987,
    "publisher": "Elsevier",
}

_BEAM_SPLITTER_DOI = "10.1016/0030-4018(87)90275-6"


class PhotonEvent:
    def __init__(self, mean_time, std_dev, port, *args, **kwargs):
        self.port = port
        self.mean_time = mean_time
        self.std_dev = std_dev
        self.args = args
        self.kwargs = kwargs


class IdealBeamSplitter(GenericDevice):
    """
    Ideal Beam Splitter Device
    """

    ports = {
        "A": Port(
            label="A",
            direction="input",
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None,
        ),
        "B": Port(
            label="B",
            direction="input",
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None,
        ),
        "C": Port(
            label="C",
            direction="output",
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None,
        ),
        "D": Port(
            label="D",
            direction="output",
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None,
        ),
    }

    properties = {
        "transmittance": {
            "type": float
            }
        }

    power_average = 0
    power_peak = 0
    reference = Reference(doi=_BEAM_SPLITTER_DOI, bib_dict=_BEAM_SPLITTER_BIB)
    processing_time = mpmath.mpf("1e-9")

    gui_icon = icon_list.BEAM_SPLITTER
    gui_tags = ["ideal"]
    gui_name = "Ideal Beam Splitter"
    gui_documentation = "ideal_beam_splitter.md"

    def __init__(self, uid=None):
        super().__init__(uid=uid)
        self.incomming_photons = []
        self.scheduled_event_time = None
        print("again the properties", self.properties)

    @schedule_next_event
    @log_action
    def des(self, time, *args, **kwargs):
        # Check if this call is for processing or for scheduling
        if kwargs.get("process_now", False):
            self.process_delayed_events(time)
        signals = kwargs.get("signals", {})
        if "A" in signals:
            envelope_A = signals["A"].contents
        else:
            envelope_A = Envelope()
        if "B" in signals:
            envelope_B = signals["B"].contents
        else:
            envelope_B = Envelope()

        operation = Operation(CompositeOperationType.NonPolarizingBeamSplitter,
            eta = self.properties["transittance"].get("value", jnp.pi/4))
        ce = CompositeEnvelope(envelope_A, envelope_B)
        ce.apply_operation(operation, envelope_A.fock, envelope_B.fock)
        signalC = GenericQuantumSignal()
        signalC.set_contents(content=envelope_A)
        signalD = GenericQuantumSignal()
        signalD.set_contents(content=envelope_B)
        result = [
            ("C", signalC, time+IdealBeamSplitter.processing_time),
            ("D", signalC, time+IdealBeamSplitter.processing_time)
            ]
            
