"""
Unit Cell
"""

from photon_weave.state.envelope import Envelope

from qureed.devices import (
    GenericDevice,
    ensure_output_compute,
    log_action,
    schedule_next_event,
    wait_input_compute,
)
from qureed.devices.port import Port
from qureed.extra.logging import Loggers, get_custom_logger
from qureed.gui.icons import icon_list
from qureed.signals import GenericBoolSignal, GenericQuantumSignal
from qureed.simulation import ModeManager, Simulation, SimulationType

logger = get_custom_logger(Loggers.Devices)


class UnitCell(GenericDevice):
    """
    Implements Unit Cell
    """

    ports = {
        "input": Port(
            label="input",
            direction="input",
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None,
        ),
        "control": Port(
            label="control",
            direction="input",
            signal=None,
            signal_type=GenericBoolSignal,
            device=None,
        ),
        "output": Port(
            label="output",
            direction="output",
            signal=None,
            signal_type=GenericQuantumSignal,
            device=None,
        ),
    }

    # Gui Configuration
    gui_icon = icon_list.FIBER
    gui_tags = ["ideal"]
    gui_name = "Unit Cell"
    gui_documentation = "unit_cell.md"

    power_average = 0
    power_peak = 0
    reference = None

    @wait_input_compute
    def compute_outputs(self, *args, **kwargs):
        self.ports["output"].signal.set_contents(
            timestamp=0, mode_id=self.ports["input"].signal.mode_id
        )

    @log_action
    @schedule_next_event
    def des_action(self, time=None, *args, **kwargs):
        env = kwargs["signals"]["input"].signal.contents
        signal = GenericQuantumSigna()
        signal.set_contents(content=env)
        result = [("output", signal, time + 1)]
        return results
