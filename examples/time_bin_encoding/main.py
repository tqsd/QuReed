import jax.numpy as jnp
import logging
from qureed.devices.clocks import ConstantClock
from qureed.devices.optical_sources import IdealNPhotonSource
from qureed.devices.phase_shifters import IdealPhaseShifter
from qureed.devices.beam_splittters import PerfectOverlapBeamSplitter
from qureed.devices.detectors import IdealDetector, ImperfectDetector
from qureed.logging import setup_logger, LoggerCategory
from custom_tbe_measurement import TBEMeasurement
from qureed.simulation.simulation import Simulation


def time_bin_encoding(alpha: float, beta: float):
    # FREQUENCY OF SENDING PULSES
    FREQUENCY = 1000  # /second
    clk = ConstantClock()
    clk.set_property("name", "CLK")
    clk.set_property("frequency", FREQUENCY)
    sps = IdealNPhotonSource()
    sps.set_property("photonNum", 1)
    sps.set_property("name", "SPS")

    ps1 = IdealPhaseShifter()
    ps1.set_property("phi", float(alpha))
    ps1.set_property("name", "PS1")

    bs1 = PerfectOverlapBeamSplitter()
    bs1.set_property("name", "BS1")

    bs2 = PerfectOverlapBeamSplitter()
    bs2.set_property("name", "BS2")

    det = IdealDetector()
    det.set_property("name", "DET")

    ps2 = IdealPhaseShifter()
    ps2.set_property("phi", float(beta))
    ps2.set_property("name", "PS2")

    bs3 = PerfectOverlapBeamSplitter()
    bs3.set_property("name", "BS3")
    bs4 = PerfectOverlapBeamSplitter()
    bs4.set_property("name", "BS4")

    clk_measurement = ConstantClock()
    clk_measurement.set_property("name", "CLK_M")
    clk_measurement.set_property("frequency", FREQUENCY)

    detA = ImperfectDetector()
    detB = ImperfectDetector()
    # Set the imperfections
    detA.set_property("deadTime", 5e-9)
    detB.set_property("deadTime", 5e-9)

    detA.set_property("detectorJitter", 1e-9)
    detB.set_property("detectorJitter", 1e-9)

    detA.set_property("darkCountRateHz", 1e5)  # 10 MHz dark counts
    detB.set_property("darkCountRateHz", 1e5)
    # detA = IdealDetector()
    # detB = IdealDetector()

    m = TBEMeasurement()
    m.set_property("name", "TBE MEASURE")
    # CONNECTS

    # > Source
    clk.connect(clk.Ports.tick, sps, sps.Ports.trigger)

    # Source > First MZI
    sps.connect(sps.Ports.output, bs1, bs1.Ports.B)

    # > First MZI
    bs1.connect(bs1.Ports.C, ps1, ps1.Ports.input)
    bs1.connect(bs1.Ports.D, bs2, bs2.Ports.B)
    ps1.connect(ps1.Ports.output, bs2, bs2.Ports.A)

    # First MZI > Second MZI
    bs2.connect(bs2.Ports.C, bs3, bs3.Ports.A)
    # We measure the escaped signal, due to loss to the environment
    bs2.connect(bs2.Ports.D, det, det.Ports.input)

    # > Second MZI
    bs3.connect(bs3.Ports.C, ps2, ps2.Ports.input)
    bs3.connect(bs3.Ports.D, bs4, bs4.Ports.B)
    ps2.connect(ps2.Ports.output, bs4, bs4.Ports.A)

    # Second MZI > Measurement
    bs4.connect(bs4.Ports.C, detA, detA.Ports.input)
    bs4.connect(bs4.Ports.D, detB, detB.Ports.input)

    # Detectors > Measurement Device
    detA.connect(detA.Ports.output, m, m.Ports.A)
    detB.connect(detB.Ports.output, m, m.Ports.B)

    # > Measurement
    clk_measurement.connect(clk_measurement.Ports.tick, m, m.Ports.clk)

    sim = Simulation()
    # Device based logs configuration
    # sim.enable_logging(name_contains="perfect")
    sim.enable_logging(name_contains="TBE")
    sim.enable_logging(name_contains="DET")
    Simulation().run(until=0.01)

    # Create a plot
    # Flatten the measurements into a list
    m.plot()


if __name__ == "__main__":
    # Set up the loggers
    # Change logging level to logging.DEBUG to enable the logs
    setup_logger(LoggerCategory.GLOBAL, level=logging.WARNING)
    setup_logger(LoggerCategory.FLOW, level=logging.WARNING)
    time_bin_encoding(jnp.pi / 2, 0)
