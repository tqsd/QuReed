"""
Ideal Beam Splitter
"""

import heapq
import mpmath
import jax.numpy as jnp

from quasi.devices.generic_device import (
    GenericDevice,
    log_action,
    ensure_output_compute,
    schedule_next_event,
    wait_input_compute,
)
from quasi.devices.port import Port
from quasi.simulation import Simulation
from quasi.extra import Reference
from quasi.signals import GenericQuantumSignal
from quasi.gui.icons import icon_list

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

    power_average = 0
    power_peak = 0
    reference = Reference(doi=_BEAM_SPLITTER_DOI, bib_dict=_BEAM_SPLITTER_BIB)
    processing_time = mpmath.mpf("1e-9")

    gui_icon = icon_list.BEAM_SPLITTER
    gui_tags = ["ideal"]
    gui_name = "Ideal Beam Splitter"
    gui_documentation = "ideal_beam_splitter.md"

    def __init__(self, name=None, uid=None):
        super().__init__(name=name, uid=uid)
        self.incomming_photons = []
        self.scheduled_event_time = None

    @ensure_output_compute
    @wait_input_compute
    def compute_outputs(self):
        """
        Waits for the input singlas to be computed
        and then the outputs are computed by this method
        """
        pass

    @schedule_next_event
    @log_action
    def des(self, time, *args, **kwargs):
        # Check if this call is for processing or for scheduling
        if kwargs.get("process_now", False):
            self.process_delayed_events(time)
        signals = kwargs.get("signals", {})
        new_events = []
        if "A" in signals:
            envelope_A = signals["A"].contents
            std_dev_A = envelope_A.temporal_profile.get_std_dev()
            new_events.append(PhotonEvent(time, std_dev_A, "A", signals=signals))
        if "B" in signals:
            envelope_B = signals["B"].contents
            std_dev_B = envelope_B.temporal_profile.get_std_dev()
            new_events.append(PhotonEvent(time, std_dev_B, "B", signals=signals))

        self.incomming_photons.extend(new_events)
        if new_events:
            delay_time = max(
                mpmath.mpf(10) * mpmath.mpf(event.std_dev) ** 2 for event in new_events
            )
            print(f"Delay Time: {delay_time}")
            new_scheduled_time = mpmath.mpf(time) + delay_time
            if (
                self.scheduled_event_time is None
                or new_scheduled_time > self.scheduled_event_time
            ):
                self.scheduled_event_time = new_scheduled_time
                simulation = Simulation.get_instance()
                simulation.schedule_event(
                    self.scheduled_event_time, self, process_now=True
                )

    @schedule_next_event
    def process_delayed_events(self, time):
        results = []
        if len(self.incomming_photons) == 1:
            pe = self.incomming_photons[0]
            env1 = pe.kwargs["signals"][pe.port].contents
            env2 = Envelope()
            ce = CompositeEnvelope(env1, env2)
            op = CompositeOperation(CompositeOperationType.NonPolarizingBeamSplit)
            if pe.port == "A":
                ce.apply_operation(op, env1.fock, env2.fock)
                sig1 = GenericQuantumSignal()
                sig1.set_contents(env1)
                sig2 = GenericQuantumSignal()
                sig2.set_contents(env2)
            else:
                ce.apply_operation(op, env2.fock, env1.fock)
                sig1 = GenericQuantumSignal()
                sig1.set_contents(env2)
                sig2 = GenericQuantumSignal()
                sig2.set_contents(env1)

            results.append(
                ("C", sig1, pe.mean_time + IdealBeamSplitter.processing_time)
            )
            results.append(
                ("D", sig2, pe.mean_time + IdealBeamSplitter.processing_time)
            )

        elif len(self.incomming_photons) > 1:
            for i in range(len(self.incomming_photons)):
                for j in range(i + 1, len(self.incomming_photons)):
                    p1 = self.incomming_photons[i]
                    p2 = self.incomming_photons[j]

                    if p1.port != p2.port:
                        time_dif = abs(p1.mean_time - p2.mean_time)
                        env1 = p1.kwargs["signals"][p1.port].contents
                        env2 = p2.kwargs["signals"][p2.port].contents

                        ce = CompositeEnvelope(env1, env2)
                        op = Operation(
                            CompositeOperationType.NonPolarizingBeamSplit,
                            eta=jnp.pi/4,
                        )
                        if p1.port == "A":
                            ce.apply_operation(op, env1.fock, env2.fock)
                            sig1 = GenericQuantumSignal()
                            sig1.set_contents(env1)
                            sig2 = GenericQuantumSignal()
                            sig2.set_contents(env2)
                        else:
                            ce.apply_operation(op, env2.fock, env1.fock)
                            sig1 = GenericQuantumSignal()
                            sig1.set_contents(env2)
                            sig2 = GenericQuantumSignal()
                            sig2.set_contents(env1)
                        results.append(
                            (
                                "C",
                                sig1,
                                p1.mean_time + IdealBeamSplitter.processing_time,
                            )
                        )
                        results.append(
                            (
                                "D",
                                sig2,
                                p2.mean_time + IdealBeamSplitter.processing_time,
                            )
                        )
        self.incomming_photons = []
        return results
