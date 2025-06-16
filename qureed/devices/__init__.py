"""
Module __init__ file
"""

from .generic_device import GenericDevice
from .wrappers import des_proc

# from .port import connect_ports
from .port import Port

from .clocks import GenericClockDevice, ConstantClock
from .optical_sources import GenericOpticalSourceDevice, IdealNPhotonSource
from .detectors import GenericDetectorDevice, IdealDetector
from .phase_shifters import GenericPhaseShifter


# FOR PUBLISHING
from .beam_splittters import PUBLISHED_DEVICES as BEAM_SPLITTERS
from .clocks import PUBLISHED_DEVICES as CLOCKS
from .detectors import PUBLISHED_DEVICES as DETECTORS
from .fibers import PUBLISHED_DEVICES as FIBERS
from .optical_sources import PUBLISHED_DEVICES as OPTICAL_SOURCES
from .phase_shifters import PUBLISHED_DEVICES as PHASE_SHIFTERS
from .waveplates import PUBLISHED_DEVICES as WAVEPLATES

BUILTIN_DEVICES = []

for cls in BEAM_SPLITTERS:
    BUILTIN_DEVICES.append((cls, "BeamSplitters"))
for cls in CLOCKS:
    BUILTIN_DEVICES.append((cls, "Clocks"))
for cls in DETECTORS:
    BUILTIN_DEVICES.append((cls, "Detectors"))
for cls in FIBERS:
    BUILTIN_DEVICES.append((cls, "Fibers"))
for cls in OPTICAL_SOURCES:
    BUILTIN_DEVICES.append((cls, "OpticalSources"))
for cls in PHASE_SHIFTERS:
    BUILTIN_DEVICES.append((cls, "PhaseShifters"))
for cls in WAVEPLATES:
    BUILTIN_DEVICES.append((cls, "Waveplates"))

__all__ = [
    "GenericDevice",
    "des_proc",
    "Port",
    "GenericClockDevice",
    "ConstantClock",
    "GenericOpticalSourceDevice",
    "IdealNPhotonSource",
    "GenericDetectorDevice",
    "IdealDetector",
    "GenericPhaseShifter",
]
