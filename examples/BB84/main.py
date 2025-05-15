from qureed.simulation import Simulation
from qureed.devices.clocks.constant_clock import ConstantClock
from qureed.devices.optical_sources.ideal_n_photon_source import (
    IdealNPhotonSource,
)
from qureed.devices.waveplates.ideal_tunable_waveplate import (
    IdealTunableWaveplate,
)
from random_basis_trigger import RandomBasisTrigger
from random_basis_detection import RandomBasisDetection


def BB84():
    FREQUENCY = 10
    # ALICE DEVICES
    A_clock = ConstantClock()
    A_clock.set_property("frequency", FREQUENCY)
    A_rbt = RandomBasisTrigger()
    A_rbt.set_property("frequency", FREQUENCY)
    A_sps = IdealNPhotonSource()
    A_itwp = IdealTunableWaveplate()

    # ALICE CONNECTS
    A_clock.connect(A_clock.Ports.tick, A_rbt, A_rbt.Ports.clk)
    A_rbt.connect(A_rbt.Ports.random, A_itwp, A_itwp.Ports.control)
    A_rbt.connect(A_rbt.Ports.trigger, A_sps, A_sps.Ports.trigger)
    A_sps.connect(A_sps.Ports.output, A_itwp, A_itwp.Ports.input)

    # BOB DEVICES
    B_clock = ConstantClock()
    B_clock.set_property("frequency", FREQUENCY)
    B_rbd = RandomBasisDetection()
    B_itwp = IdealTunableWaveplate()

    # BOB CONNECTS
    B_clock.connect(B_clock.Ports.tick, B_rbd, B_rbd.Ports.clk)
    B_rbd.connect(B_rbd.Ports.rnd, B_itwp, B_itwp.Ports.control)
    B_itwp.connect(B_itwp.Ports.output, B_rbd, B_rbd.Ports.input)

    # INTERCONNECT
    A_itwp.connect(A_itwp.Ports.output, B_itwp, B_itwp.Ports.input)

    Simulation().run(until=1)
    print(A_rbt._sent_bits)
    print(B_rbd._measured_bits)


if __name__ == "__main__":
    BB84()
