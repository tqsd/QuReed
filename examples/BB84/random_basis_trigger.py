from typing import Dict, Any
import math
import random
from enum import Enum
from qureed.devices import GenericDevice
from qureed.devices.port import Port
from qureed.devices.wrappers import des_proc
from qureed.signals.trigger_signal import TriggerSignal
from qureed.signals.value_signals import FloatSignal

from basis_confirmation_signal import BasisConfirmSignal


class RandomBasisTrigger(GenericDevice):
    """
    Random Basis Trigger Device (Alice)

    This example device implements the sender (Alice) in the BB84 quantum key
    distribution protocol. On each clock cycle, it generates a random bit and
    randomly chooses one of two polarization bases (rectilinear or diagonal).
    It then emits the appropriate rotation angle to a waveplate and triggers
    the emission of a single-photon pulse.

    After receiving a basis comparison signal fro Bob, it confirms which bits
    were measured in the same basis and appends them to its shared secret key.

    Ports:
    ------
    - clk (input): `TriggerSignal`
        Clock input to trigger new bit + basis generation.
    - random (output): `FloatSignal`
        Rotation angle for the tunable waveplate, based on selected bit and
        basis.
    - trigger (output): `TriggerSignal`
        Trigger output to activate the single-photon source.
    - basis_confirm_in (input): `BasisConfirmSignal`
        Receives the list of Bob’s bases to compare with sent bits.
    - basis_confirm_out (output): `BasisConfirmSignal`
        Sends confirmation to Bob about which basis matches occurred.

    Properties:
    -----------
    - frequency: float
        Clock frequency in Hz. Used to time the bit/basis generation and
        signal transmission.

    Attributes:
    -----------
    - _sent_bits (list[Tuple[int, int]]):
        A buffer of sent (basis, bit) pairs that await basis confirmation.
    - quantum_key (list[int]):
        Final shared key bits that were confirmed by Bob.

    Example:
    --------
    >>> alice = RandomBasisTrigger()
    >>> alice.set_property("frequency", 10)
    >>> # during simulation: alice.quantum_key will contain the final key bits
    """

    properties: Dict[str, Dict[str, Any]] = {"frequency": {"type": float}}

    @property
    def gui_name(self) -> str:
        return "Random Basis Trigger"

    @property
    def gui_icon(self) -> str:
        return "None"

    # <<< static hint for LSP autocomplete >>>
    class Ports(Enum):
        clk = "clk"
        random = "random"
        trigger = "trigger"
        basis_confirm_in = "basis_confirm_in"
        basis_confirm_out = "basis_confirm_out"

    # <<< end of type hint >>>

    port_definitions = {
        "clk": Port(direction="input", signal_type=TriggerSignal),
        "random": Port(direction="output", signal_type=FloatSignal),
        "trigger": Port(direction="output", signal_type=TriggerSignal),
        "basis_confirm_in": Port(
            direction="input", signal_type=BasisConfirmSignal
        ),
        "basis_confirm_out": Port(
            direction="output", signal_type=BasisConfirmSignal
        ),
    }

    def __init__(self, uid=None, **kwargs):
        super().__init__(uid, **kwargs)
        self._sent_bits = []
        self.quantum_key = []

    @des_proc
    def proc(self):
        """
        Bit and basis generation process.

        On each clock cycle, generates a random bit and randomly selects
        either the Z (rectilinear) or X (diagonal) polarization basis.

        Based on the selected bit and basis, computes the corresponding
        RY rotation angle:
        - Z basis: 0 (|H⟩) or π (|V⟩)
        - X basis: +π/2 (|D⟩) or -π/2 (|A⟩)

        Emits the angle via the `random` port to a tunable waveplate and
        triggers a photon emission via the `trigger` port.
        """
        send_delay = 1 / (10 * self.get_property("frequency"))
        while True:
            yield self.receive(self.Ports.clk)
            yield self.sim_env.timeout(send_delay)

            basis = random.randint(0, 1)
            bit = random.randint(0, 1)
            self._sent_bits.append((basis, bit))

            if basis == 0:
                angle = 0 if bit == 0 else math.pi
            else:
                angle = math.pi / 2 if bit == 0 else -math.pi / 2

            self.send(self.Ports.random, FloatSignal(value=angle))
            yield self.sim_env.timeout(send_delay)
            self.send(self.Ports.trigger, TriggerSignal())

    @des_proc
    def basis_confirmation(self):
        """
        Receives Bob's basis list and sends back confirmation.

        When a `BasisConfirmSignal` is received from Bob, compares it against
        the locally stored `_sent_bits`. For each index, if the bases match,
        the corresponding bit is appended to the shared `quantum_key`, and
        a `1` is returned in the confirmation list; otherwise `0`.

        Afterward, sends back the confirmation list to Bob and clears the
        corresponding entries from the buffer.
        """
        while True:
            signal = yield self.receive(self.Ports.basis_confirm_in)
            remote_basis = signal.basis
            volatile_keys = self._sent_bits[: len(remote_basis)]
            del self._sent_bits[: len(remote_basis)]
            correct_basis = []
            for i, base in enumerate(remote_basis):
                if base == volatile_keys[i][0]:
                    correct_basis.append(1)
                    self.quantum_key.append(volatile_keys[i][1])
                else:
                    correct_basis.append(0)
            self.send(
                self.Ports.basis_confirm_out,
                BasisConfirmSignal(confirmation=correct_basis),
            )
