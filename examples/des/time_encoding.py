from qureed.simulation import Simulation
from qureed.devices.control import SimpleTrigger
from qureed.devices.sources import IdealNPhotonSource
from qureed.devices.fiber import IdealFiber
from qureed.devices.detectors import IdealDetector
from qureed.devices.beam_splitters import IdealBeamSplitter
from qureed.signals import GenericBoolSignal, GenericQuantumSignal, GenericIntSignal
import mpmath


# Helper function for connecting devices with signals
def connect(sig_cls, dev1, port1, dev2=None, port2=None):
    sig = sig_cls()
    dev1.register_signal(signal=sig, port_label=port1)
    if dev2 is not None and port2 is not None:
        dev2.register_signal(signal=sig, port_label=port2)
    return sig


# Devices
trigger = SimpleTrigger("Trigger", time=0)
source = IdealNPhotonSource("Source")
bs1 = IdealBeamSplitter("BS1")
f1 = IdealFiber("Fiber")
f1.set_length(1000)

# connecting
signals = {}
signals["qsig1"] = connect(GenericBoolSignal, trigger, "trigger", source, "trigger")
signals["qsig2"] = connect(GenericQuantumSignal, source, "output", f1, "input")
signals["qsig3"] = connect(GenericQuantumSignal, f1, "output", bs1, "A")
signals["photon_num"] = connect(GenericIntSignal, source, "photon_num")
signals["photon_num"].set_int(3)

if __name__ == "__main__":
    simulation = Simulation.get_instance()
    simulation.run_des(1)
