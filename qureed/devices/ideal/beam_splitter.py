"""
Ideal Beam Splitter
"""

import heapq

import mpmath

from qureed.devices.generic_device import (
    GenericDevice,
    ensure_output_compute,
    log_action,
    schedule_next_event,
    wait_input_compute,
)
from qureed.devices.port import Port
from qureed.extra import Reference
from qureed.signals import GenericQuantumSignal
from qureed.simulation import Simulation

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
    def __init__(self, mean_time, std_dev, *args, **kwargs):
        self.mean_time = mean_time
        self.std_dev = std_dev
        self.args = args
        self.kwargs = kwargs


class IdealBeamSplitter(GenericDevice):
    """
    Ideal Beam Splitter Device
    """

    power_average = 0
    power_peak = 0
    reference = Reference(doi=_BEAM_SPLITTER_DOI, bib_dict=_BEAM_SPLITTER_BIB)

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
            return
        signals = kwargs.get("signals", {})
        new_events = []

        if "A" in signals:
            envelope_A = signals["A"].contents
            std_dev_A = envelope_A.get_std_dev()
            new_events.append(PhotonEvent(time, std_dev_A, "A"))
        if "B" in signals:
            envelope_B = signals["A"].contents
            std_dev_B = envelope_A.get_std_dev()
            new_events.append(PhotonEvent(time, std_dev_B, "B"))

        self.incomming_photons.extend(new_events)
        if new_events:
            delay_time = max(10 * event.std_dev**2 for event in new_events)
            new_scheduled_time = time + delay_time
            if (
                scheduled_event_time is None
                or new_scheduled_time > self.scheduled_event_time
            ):
                self.scheduled_event_time = new_scheduled_time
                simulation = Simulation.get_instance()
                simulation.schedule_event(
                    self.scheduled_event_time, self, process_now=True
                )
