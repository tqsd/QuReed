from typing import Dict, Any, cast

from .generic_detector import GenericDetectorDevice
from qureed.signals import IntSignal, QuantumOpticalPulseSignal, QOPSignalType


class ImperfectDetector(GenericDetectorDevice):
    properties: Dict[str, Dict[str, Any]] = {
        "delay": {"type": float, "value": 1e-9},
        "detectorJitter": {"type": float, "value": 30e-12},
        "enableEnvelopeJitter": {"type": bool, "value": True},
        "darkCountRateHz": {"type": float, "value": 0.0},
        "deadTime": {"type": float, "value": 0.0},
    }

    @property
    def gui_name(self) -> str:
        return "Imperfect Detector"
