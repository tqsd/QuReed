import logging

from qureed.devices.beam_splittters.perfect_overlap_beamsplitter import (
    PerfectOverlapBeamSplitter,
)
from qureed.devices.clocks.constant_clock import ConstantClock
from qureed.devices.optical_sources.ideal_n_photon_source import (
    IdealNPhotonSource,
)
from qureed.devices.phase_shifters.ideal_phase_shifter import IdealPhaseShifter
from qureed.logging.core import setup_logger
from qureed.logging.loggers import LoggerCategory
from qureed.simulation.simulation import Simulation


setup_logger(LoggerCategory.GLOBAL, level=logging.DEBUG)
setup_logger(LoggerCategory.FLOW, level=logging.DEBUG)

if __name__ == "__main__":
    FREQUENCY = 2
    clk = ConstantClock()
    clk.set_property("frequency", FREQUENCY)
    clk.set_property("name", "CLK")

    sps = IdealNPhotonSource()
    sps.set_property("name", "SPS")

    ps = IdealPhaseShifter()
    ps.set_property("name", "PS")
    ps.set_property("phi", 0)

    bs1 = PerfectOverlapBeamSplitter()
    bs1.set_property("name", "BS1")
    bs2 = PerfectOverlapBeamSplitter()
    bs2.set_property("name", "BS2")
    bs2._inboxes["B"].debug = True

    clk.connect(clk.Ports.tick, sps, sps.Ports.trigger)
    sps.connect(sps.Ports.output, bs1, bs1.Ports.A)
    bs1.connect(bs1.Ports.C, ps, ps.Ports.input)
    ps.connect(ps.Ports.output, bs2, bs2.Ports.A)
    bs1.connect(bs1.Ports.D, bs2, bs2.Ports.B)

    sim = Simulation()
    sim.enable_logging(name_contains="BS1")
    sim.run(until=1)
