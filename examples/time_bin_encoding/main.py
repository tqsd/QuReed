import jax.numpy as jnp
import logging
from qureed.constants import C0
from qureed.devices.clocks import ConstantClock
from qureed.devices.fibers.lossy_fiber import LossyFiber
from qureed.devices.optical_sources import IdealNPhotonSource
from qureed.devices.phase_shifters import IdealPhaseShifter
from qureed.devices.beam_splittters import PerfectOverlapBeamSplitter
from qureed.devices.detectors import IdealDetector, ImperfectDetector
from qureed.logging import setup_logger, LoggerCategory
from custom_tbe_measurement import TBEMeasurement
from qureed.simulation.simulation import Simulation


def fiber_length_for_delay(delta_t: float, n: float) -> float:
    """
    Helper function to compute lenght from given delay and
    refractive index
    """
    return (C0 / n) * delta_t


def validate_tbe_config(
    frequency_hz: float,
    first_pulse_delay: float,
    pulse_spacing: float,
    time_tolerance: float,
    num_pulses: int = 3,
    dead_time: float | None = None,
    detector_jitter: float | None = None,
) -> None:
    """
    Validates that time-bin gates do not overlap and fit within one round.
    Raises ValueError with a helpful message if constraints are violated.
    """
    if pulse_spacing <= 0:
        raise ValueError("pulse_spacing must be > 0.")
    if time_tolerance <= 0:
        raise ValueError("time_tolerance must be > 0.")
    if frequency_hz <= 0:
        raise ValueError("frequency must be > 0.")
    if first_pulse_delay < time_tolerance:
        logging.warning(
            "[TBE config] first_pulse_delay (%.3e s) < time_tolerance (%.3e s). "
            "The first gate will extend before the round start, which is usually fine.",
            first_pulse_delay,
            time_tolerance,
        )
    # No overlap condition: centers are t0 + k*Δ; ensure 2*tol ≤ Δ
    if pulse_spacing < 2 * time_tolerance:
        raise ValueError(
            f"pulse_spacing ({
                pulse_spacing}) must be >= 2 * time_tolerance ({2*time_tolerance}) "
            "to avoid overlapping gates."
        )

    period = 1.0 / frequency_hz
    last_center = first_pulse_delay + (num_pulses - 1) * pulse_spacing
    # Must fit: last gate must end before period
    if last_center + time_tolerance > period:
        # Suggest max frequency that would make it fit exactly
        max_ok_freq = 1.0 / (last_center + time_tolerance)
        raise ValueError(
            "Gates overflow the round period.\n"
            f"- last_center + tol = {last_center +
                                     time_tolerance:.6e} s > period = {period:.6e} s\n"
            f"- Reduce FREQUENCY to ≤ {
                max_ok_freq:.3f} Hz, or reduce first_pulse_delay/pulse_spacing/time_tolerance."
        )

    # Optional sanity hints (non-fatal)
    hints = []
    if dead_time is not None:
        # Effective per-bin listen is ~2*tol; ensure dead time << gap to next gate
        if dead_time >= (pulse_spacing - 2 * time_tolerance):
            hints.append(
                f"deadTime ({dead_time:.3e}s) ≥ pulse_spacing - 2*tol "
                f"({pulse_spacing - 2*time_tolerance:.3e}s). "
                "A click may suppress the next-bin click due to dead time."
            )
    if detector_jitter is not None:
        # Rule of thumb: tol should be several σ of jitter
        if time_tolerance < 3 * detector_jitter:
            hints.append(
                f"time_tolerance ({time_tolerance:.3e}s) < ~3×detectorJitter ({
                    3*detector_jitter:.3e}s). "
                "Consider increasing tolerance or reducing jitter; mis-binning risk is higher."
            )
    for h in hints:
        logging.warning("[TBE config] " + h)


def time_bin_encoding(alpha: float, beta: float):
    # FREQUENCY OF SENDING PULSES
    FREQUENCY = 2000  # /second
    N_FIBER = 1.45  # refractive index for the fiber
    MZI_DELAY = 50e-6  # delay introduced by the fiber in the long arm
    TIME_TOLERANCE = 12.5e-6
    LENGTH = fiber_length_for_delay(MZI_DELAY, N_FIBER)
    DEAD_TIME = 24e-6  # 25e-6
    DETECTOR_JITTER = 200e-12
    DARK_COUNT_HZ = 10000

    validate_tbe_config(
        frequency_hz=FREQUENCY,
        first_pulse_delay=6e-9,  # you use this below in configure_timing
        pulse_spacing=MZI_DELAY,
        time_tolerance=TIME_TOLERANCE,
        num_pulses=3,
        dead_time=DEAD_TIME,
        detector_jitter=DETECTOR_JITTER,
    )
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

    # We add an ideal fiber without phase shift to control the time delay
    fib1 = LossyFiber()
    fib1.set_property("name", "FIB1")
    fib1.set_property("length", LENGTH)
    fib1.set_property("loss", 0.0)
    fib1.set_property("phaseShift", False)

    fib2 = LossyFiber()
    fib2.set_property("name", "FIB2")
    fib2.set_property("length", LENGTH)
    fib2.set_property("loss", 0.0)
    fib2.set_property("phaseShift", False)

    bs2 = PerfectOverlapBeamSplitter()
    bs2.set_property("name", "BS2")

    det = IdealDetector()
    det.set_property("name", "DUMP")

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

    detA.set_property("name", "DET A")
    detB.set_property("name", "DET B")

    # Set the imperfections
    deadTime = DEAD_TIME
    detA.set_property("deadTime", deadTime)
    detB.set_property("deadTime", deadTime)

    detectorJitter = DETECTOR_JITTER
    detA.set_property("detectorJitter", detectorJitter)
    detB.set_property("detectorJitter", detectorJitter)

    darkCountRateHz = DARK_COUNT_HZ
    detA.set_property("darkCountRateHz", darkCountRateHz)
    detB.set_property("darkCountRateHz", darkCountRateHz)
    # detA = IdealDetector()
    # detB = IdealDetector()

    m = TBEMeasurement()
    m.configure_timing(
        first_pulse_delay=6e-9,
        pulse_spacing=MZI_DELAY,
        time_tolerance=TIME_TOLERANCE,
    )
    m.set_property("name", "TBE MEASURE")
    # CONNECTS

    # > Source
    clk.connect(clk.Ports.tick, sps, sps.Ports.trigger)

    # Source > First MZI
    sps.connect(sps.Ports.output, bs1, bs1.Ports.B)

    # > First MZI
    bs1.connect(bs1.Ports.C, fib1, fib1.Ports.input)
    fib1.connect(fib1.Ports.output, ps1, ps1.Ports.input)
    bs1.connect(bs1.Ports.D, bs2, bs2.Ports.B)
    ps1.connect(ps1.Ports.output, bs2, bs2.Ports.A)

    # First MZI > Second MZI
    bs2.connect(bs2.Ports.C, bs3, bs3.Ports.A)
    # We measure the escaped signal, due to loss to the environment
    bs2.connect(bs2.Ports.D, det, det.Ports.input)

    # > Second MZI
    bs3.connect(bs3.Ports.C, fib2, fib2.Ports.input)
    bs3.connect(bs3.Ports.D, bs4, bs4.Ports.B)
    fib2.connect(fib2.Ports.output, ps2, ps2.Ports.input)
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
    sim.enable_logging(name_contains="FIB")
    Simulation().run(until=0.1)

    # Create a plot
    # Flatten the measurements into a list
    fig = m.plot()
    fig.savefig(f"DC={DARK_COUNT_HZ}_DT={DEAD_TIME}.png")


if __name__ == "__main__":
    # Set up the loggers
    # Change logging level to logging.DEBUG to enable the logs
    setup_logger(LoggerCategory.GLOBAL, level=logging.WARNING)
    setup_logger(LoggerCategory.FLOW, level=logging.WARNING)
    time_bin_encoding(jnp.pi / 2, 0)
