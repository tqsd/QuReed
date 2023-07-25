"""
Ideal Beam Splitter experiment example
"""

from quasi.simulation import Simulation
from quasi.devices.ideal import BeamSplitter
from quasi.devices.ideal import SinglePhotonSource
from quasi.devices.ideal import SinglePhotonDetector
from quasi.devices.ideal import Fiber
from quasi.devices import connect_ports

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

Sim.list_devices()

"""       ╭────────────────────╮ 
          │  EXPERIMENT SETUP  │
          ╰────────────────────╯
"""

# Connect the devices
connect_ports(sps1.ports["OUT"],fib1.ports["IN"])
connect_ports(sps2.ports["OUT"],fib2.ports["IN"])
connect_ports(fib1.ports["OUT"],bs.ports["A"])
connect_ports(fib2.ports["OUT"],bs.ports["B"])
connect_ports(bs.ports["C"],fib3.ports["IN"])
connect_ports(bs.ports["D"],fib4.ports["IN"])
connect_ports(fib3.ports["IN"],spd1.ports["IN"])
connect_ports(fib4.ports["IN"],spd2.ports["IN"])


"""       ╭────────────────────╮ 
          │   RUN SIMULATION   │
          ╰────────────────────╯
"""

Sim.run()
