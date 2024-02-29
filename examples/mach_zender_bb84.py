"""
Mach Zender BB84 implementation
"""
from quasi.simulation import Simulation, SimulationType, ModeManager
from quasi.devices.sources import IdealNPhotonSource, IdealCoherentSource
from quasi.devices.control import SimpleTrigger
from quasi.devices.beam_splitters import IdealBeamSplitter
from quasi.devices.phase_shifters import IdealPhaseShifter
from quasi.signals import GenericBoolSignal, GenericQuantumSignal
from quasi.experiment import Experiment
from quasi.backend.fock_first_backend import FockBackendFirst
from quasi._math.fock import ops

# Import Custom Phase Shift
from custom_phase_shifter_device import CustomPhaseShift

import numpy as np
from math import pi
np.set_printoptions(suppress=True)
np.set_printoptions(linewidth=200)

sim = Simulation()
sim.set_backend(FockBackendFirst())
sim.set_dimensions(3)

# Create all of the devices
BSa = IdealBeamSplitter("BSa")
BSb = IdealBeamSplitter("BSb")
BSc = IdealBeamSplitter("BSc")
BSd = IdealBeamSplitter("BSd")
#PSa = IdealPhaseShifter("PSa")
PSa = CustomPhaseShift("PSa")
PSa.set_params(voltage=pi/2, A=1, B=1, C=-pi/4)
#PSa.set_phi(pi/4)

PSb = IdealPhaseShifter("PSb")
PSb.set_phi(pi/4)

S = IdealNPhotonSource("Source")
S.set_photon_num(1)
trigger = SimpleTrigger()

# Create Signals
signals = {}
signals["trigger"] = GenericBoolSignal()
signals["qsig1"] = GenericQuantumSignal()
signals["qsig2"] = GenericQuantumSignal()
signals["qsig3"] = GenericQuantumSignal()
signals["qsig4"] = GenericQuantumSignal()
signals["qsig5"] = GenericQuantumSignal()
signals["qsig6"] = GenericQuantumSignal()
signals["qsig7"] = GenericQuantumSignal()
signals["qsig8"] = GenericQuantumSignal()
signals["qsig9"] = GenericQuantumSignal()
discard_sig = GenericQuantumSignal()
# Connect trigger and source
trigger.register_signal(signal=signals["trigger"], port_label="trigger")
S.register_signal(signal=signals["trigger"], port_label="trigger")

# connect source and beam splitter a
S.register_signal(signal=signals["qsig1"], port_label="output")
BSa.register_signal(signal=signals["qsig1"], port_label="B")

# connect beam splitter a and phase shifter
BSa.register_signal(signal=signals["qsig2"], port_label="C")
PSa.register_signal(signal=signals["qsig2"], port_label="input")

# connect beam splitter a and b
BSa.register_signal(signal=signals["qsig3"], port_label="D")
BSb.register_signal(signal=signals["qsig3"], port_label="B")

# connect phase shifter and beam splitter b
PSa.register_signal(signal=signals["qsig4"], port_label="output")
BSb.register_signal(signal=signals["qsig4"], port_label="A")

# connect beamspitter b and c
BSb.register_signal(signal=signals["qsig5"], port_label="C")
BSb.register_signal(signal=signals["qsig6"], port_label="D")

#BSb.register_signal(signal=signals["qsig6"], port_label="D")

BSc.register_signal(signal=signals["qsig5"], port_label="A")
#BSc.register_signal(signal=signals["qsig6"], port_label="B")


# Connect beamsplitter c and phase shifter
BSc.register_signal(signal=signals["qsig7"], port_label="C")
PSb.register_signal(signal=signals["qsig7"], port_label="input")

# Connect phase shifter b and beam splitter d
PSb.register_signal(signal=signals["qsig8"], port_label="output")
BSd.register_signal(signal=signals["qsig8"], port_label="A")

# Connect beam splitter c and beam splitter d
BSc.register_signal(signal=signals["qsig9"], port_label="D")
BSd.register_signal(signal=signals["qsig9"], port_label="B")

# Signal going to det 1
dsig1 = GenericQuantumSignal()
dsig2 = GenericQuantumSignal()

BSd.register_signal(signal=dsig1, port_label="C")
BSd.register_signal(signal=dsig2, port_label="D")

sim.run()

exp = Experiment.get_instance()

#print(exp.state.all_fock_probs())
state = exp.state
mm = ModeManager()

print("trace")
#print(ops.calculate_trace(state))

print(mm.get_mode_index(dsig1.mode_id))

m1 = state.mean_photon(mode=[mm.get_mode_index(dsig1.mode_id)])
m2 = state.mean_photon(mode=[mm.get_mode_index(dsig2.mode_id)])

print(f"Probability of measuring photon in det 1: {m1}")
print(f"Probability of measuring photon in det 1: {m2}")

det1 = mm.get_mode_index(dsig1.mode_id)
det2 = mm.get_mode_index(dsig2.mode_id)
disc = mm.get_mode_index(signals["qsig6"].mode_id)

p1 = [0,0,0]
p1[det1] = 1
p1[det2] = 0
p1[disc] = 0

p2 = [0,0,0]
p2[det1] = 0
p2[det2] = 0
p2[disc] = 1


print(det1, det2)
print(f"Probability |1,0,0>, |det1, det2, disc>")
print(state.all_fock_probs()[*p1])
print(f"Probability |0,0,1>, |det1, det2, disc>")
print(state.all_fock_probs()[*p2])
print(state.all_fock_probs())
print(state.dm().shape)
