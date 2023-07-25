"""
Ideal Beam Splitter experiment example
"""

from quasi.simulation import Simulation
from quasi.devices.ideal import BeamSplitter
from quasi.devices.ideal import SinglePhotonSource
from quasi.devices.ideal import SinglePhotonDetector
from quasi.devices.ideal import Fiber
from quasi.devices import connect_ports
from quasi.signals import GenericQuantumSignal

Sim = Simulation()


"""       ╭───────────╮ 
          │  DEVICES  │
          ╰───────────╯
"""

# Single Photon Sources
sps1 = SinglePhotonSource(name="SPS1")
sps2 = SinglePhotonSource(name="SPS2")


# Beam Splitter
bs = BeamSplitter(name="BS")

# Detectors
spd1 = SinglePhotonDetector(name="SPD1")
spd2 = SinglePhotonDetector(name="SPD2")

# Fibers
fib1 = Fiber(name="FIB1", length=10)
fib2 = Fiber(name="FIB2", length=10)
fib3 = Fiber(name="FIB3", length=10)
fib4 = Fiber(name="FIB4", length=10)

# Prints a table of devices, registered with the simulation
# Each object instance registers itself with simulation with
# Initiation method
Sim.list_devices()

"""       ╭────────────────────╮ 
          │  EXPERIMENT SETUP  │
          ╰────────────────────╯
We should create a utility where the devices and connections
can be set up using yaml language
"""

# Connect the devices, through signals
sig1 = GenericQuantumSignal()
sps1.register_signal(signal=sig1, port_label="OUT")
fib1.register_signal(signal=sig1, port_label="IN")

sig2 = GenericQuantumSignal()
sps2.register_signal(signal=sig2, port_label="OUT")
fib2.register_signal(signal=sig2, port_label="IN")

sig3 = GenericQuantumSignal()
fib1.register_signal(signal=sig3, port_label="OUT")
bs.register_signal(signal=sig3, port_label="A")

sig4 = GenericQuantumSignal()
fib2.register_signal(signal=sig4, port_label="OUT")
bs.register_signal(signal=sig4, port_label="B")

sig5 = GenericQuantumSignal()
bs.register_signal(signal=sig5, port_label="C")
fib3.register_signal(signal=sig5, port_label="IN")

sig6 = GenericQuantumSignal()
bs.register_signal(signal=sig6, port_label="D")
fib4.register_signal(signal=sig6, port_label="IN")

sig7 = GenericQuantumSignal()
fib3.register_signal(signal=sig7, port_label="OUT")
spd1.register_signal(signal=sig7, port_label="IN")

sig8 = GenericQuantumSignal()
fib4.register_signal(signal=sig8, port_label="OUT")
spd2.register_signal(signal=sig8, port_label="IN")

# Registers which devices should be triggered when
# simulation starts
Sim.register_triggers(sps1,sps2)
Sim.list_triggered_devices()
"""       ╭────────────────────╮ 
          │   RUN SIMULATION   │
          ╰────────────────────╯
"""
Sim.set_dimensions(50)
Sim.run()
