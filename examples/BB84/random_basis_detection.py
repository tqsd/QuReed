from typing import Dict, Any
from enum import Enum
import math
import random

from qureed.devices.port import Port
from qureed.devices.wrappers import des_proc
from qureed.signals.quantum_optical_pulse_signal import (
    QOPSignalType,
    QuantumOpticalPulseSignal,
)
from qureed.signals.trigger_signal import TriggerSignal
from qureed.signals.value_signals import FloatSignal
from tests.devices.test_generic_device import GenericDevice

from basis_confirmation_signal import BasisConfirmSignal


class RandomBasisDetection(GenericDevice):
    """
    Random Basis Detection Device (Bob)

    This example device implements the receiver (Bob) in a BB84 quantum key
    distribution protocol. It randomly selects a polarization measurement
    basis (rectilinear or diagonal), applies the appropriate waveplate
    rotation, and then measures incoming quantum optical pulse signals.

    After a fixed number of measuements, it sends the basis choices to Alice
    (the sender) via `BasisConfirmSignal`. Once it receives confirmation of
    which bits match, it adds the agreed-upon bits to its quantum key.

    Ports:
    ------
    - clk (input): `TriggerSignal`
        Clock input used to trigger nwe random basis selection.
    - rnd (output): `FloatSignal`
        Output angle to be applied to a polarization waveplate to rotate into
        the chosen basis.
    - input (input): `QuantumOpticalPulseSignal`
        Quantum optical signal received from Alice.
    - basis_confirm_out (output): `BasisConfirmSignal`
        Sends this device's basis chices to Alice for comparison.
    - basis_confirm_in (input): `BasisConfirmSignal`
        Receives confirmation of which bits matched, enabling final key
        construction.

    Properties:
    -----------
    - None (currently no user-settable properties)

    Attributes:
    -----------
    - quantum_key (list[int]):
        The shared secret key bits that matched with Alice.
    - _keys_num_to_compare (int):
        Number of measurements to buffer before sending basis signal.
    - _measured_bits (list[Tuple[int, int]]):
        Local storage of measured (basis, bit) pairs awaiting confirmation.
    - _volatile_keys (list[Tuple[int, int]]):
        Temporarily holds bits waiting for confirmation response.

    Backend Compatibility:
    ----------------------
    - photon_weave: Uses `envelope.measure()` to extract measurement outcomes
      received quantum optical pulse signals.

    Example:
    --------
    >>> bob = RandomBasisDetection()
    >>> bob.quantum_key  # Final shared key after basis confirmation

    """

    properties: Dict[str, Dict[str, Any]] = {}

    @property
    def gui_name(self) -> str:
        return "Random Basis Detection"

    @property
    def gui_icon(self) -> str:
        return "None"

    # <<< static hint for LSP autocomplete >>>
    class Ports(Enum):
        clk = "clk"
        rnd = "rnd"
        input = "input"
        basis_confirm_in = "basis_confirm_in"
        basis_confirm_out = "basis_confirm_out"

    # <<< end of type hint >>>

    port_definitions = {
        "clk": Port(direction="input", signal_type=TriggerSignal),
        "rnd": Port(direction="output", signal_type=FloatSignal),
        "input": Port(
            direction="input", signal_type=QuantumOpticalPulseSignal
        ),
        "basis_confirm_out": Port(
            direction="output", signal_type=BasisConfirmSignal
        ),
        "basis_confirm_in": Port(
            direction="input", signal_type=BasisConfirmSignal
        ),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._measured_bits = []
        self._current_basis = 0
        self._keys_num_to_compare = 100
        self._volatile_keys = []
        self.quantum_key = []

    @des_proc
    def proc(self):
        """
        Clock-triggered basis selector.

        Upon receiving a `TriggerSignal` on the `clk` port, randomly selects
        either the Z (rectilinear) or X (diagonal) measurement basis. Sends the
        corresponding polarization (rotation angle) via `rnd` port.
        """
        send_delay = 1e-10
        while True:
            yield self.receive(self.Ports.clk)
            self._current_basis = random.randint(0, 1)
            angle = 0 if self._current_basis == 0 else -math.pi / 2
            yield self.sim_env.timeout(send_delay)
            self.send(self.Ports.rnd, FloatSignal(value=angle))

    @des_proc(backend="photon_weave")
    def proc_pw(self):
        """
        PhotonWeave backend: receives and measures quantum optical signals.

        Waits for `QuantumOpticalPulseSignal`s. When an `END` signal is
        received, the quantum state is measured and the bit outcome is stored.
        Once a threshold number of bits is collected (`_keys_num_to_compare`),
        the device sends out its measurement bases for confirmation.
        """
        while True:
            signal = yield self.receive(self.Ports.input)
            if signal.type is QOPSignalType.START:
                continue
            envelope = signal.payload
            outcome = envelope.measure()
            self._measured_bits.append(
                (self._current_basis, outcome[envelope.polarization])
            )
            if len(self._measured_bits) == self._keys_num_to_compare:
                self.send_basis_signal()

    def send_basis_signal(self):
        """
        Sends the current batch of measurement bases to Alice.

        This function transfers `_measured_bdits` into `_volatile_keys`, clears
        the buffer, and sends a `BasisConfirmSignal` containing the basis
        information.
        """
        self._volatile_keys[:] = self._measured_bits
        self._measured_bits.clear()

        chosen_basis = [m[0] for m in self._volatile_keys]
        self.send(
            self.Ports.basis_confirm_out,
            BasisConfirmSignal(basis=chosen_basis),
        )

    @des_proc
    def receive_confirmation_signal(self):
        """
        Receives confirmation of matching measurement bases from Alice.

        This method listens for a `BasisConfirmSignal` on the
        `basis_confirm_in` port. It compares each confirmed bit with
        corresponding basis and appends the valid bits to `quantum_key`. After
        processing, `_volatile_keys` is cleared.
        """
        while True:
            signal = yield self.receive(self.Ports.basis_confirm_in)
            confirmations = signal.confirmation
            for i, vk in enumerate(self._volatile_keys[: len(confirmations)]):
                if confirmations[i]:
                    self.quantum_key.append(vk[1])
            self._volatile_keys.clear()
