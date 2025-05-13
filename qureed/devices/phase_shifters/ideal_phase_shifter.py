from qureed.devices.wrappers import des_proc
from qureed.signals import QOPSignalType
from .generic_phase_shifter import GenericPhaseShifter


class IdealPhaseShifter(GenericPhaseShifter):
    """
    Ideal Phase Shifter Device

    The `IdeaPhaseShifter` is a simulation device for the QuReed framework
    that applies a phase shift to quantum optical signals in Fock basis.

    This component listens for the incoming `QuantumOpticalPulseSignal`s,
    and when an `END`-type signal is received, it applies a phase shift of
    an angle `phi` (in radians) to the Fock state contained in the signal.
    The phase value is configurable via the `phi` property or dynamically
    using a `FloatSignal` on the `phi` port.

    Ports:
    ------
    - input (input)   : Accepts `QuantumOpticalPulseSignal`s
    - output (output) : Emits phase-shifted `QuantumOpticalPulseSignal`s
    - phi (input)     : Accets `FloatSignal`s to dynamically update the phase

    Properties:
    -----------
    - phi: float
      declared in `GenericPhaseShifter`, phase angle (in radians) to apply
      to the Fock state. Can be set statically or updated dynamically during
      simulation.

    GUI Metadata:
    gui_name: str
        Returns "Ideal Phase Shifter" for UI display purposes.

    Backend Compatibility:
    ----------------------
    Implements a backend-specific simulation process for `photon_weave`.

    Example:
    --------
    >>> ps = IdealPhaseShifter()
    >>> ps.set_property("phi", 3.1415)
    """

    @property
    def gui_name(self) -> str:
        return "Ideal Phase Shifter"

    @des_proc(backend="photon_weave")
    def proc_pw(self):
        """
        Simulation process for the PhotonWeave backend.

        This coroutine listens for quantum optical pulse signals on the
        `input` port. It forwards `START` signals unchanged, and applies
        phase shift operation to the `Fock` state in `END` signals using
        the currently configured phase value (`phi`).

        Signal Flow:
        ------------
        - Input: `input` (`QuantumOpticalPulseSignal`)
        - Output: `output` (`QuantumOpticalPulseSignal` with phase-shifted
          `Fock` state)

        Behavior:
        ---------
        - For `START` signals: passes through unmodified.
        - For `END` signals:
          - Retrieves the current `phi` value
          - Applies a `PhaseShift` operation to the Fock state
          - Emits the modified signal to the `output` port
        """
        from photon_weave.operation import Operation, FockOperationType

        while True:
            signal = yield self.receive(self.Ports.input)
            if signal.type is QOPSignalType.START:
                self.send(self.Ports.output, signal)
            elif signal.type is QOPSignalType.END:
                phi = float(self.get_property("phi"))
                ps_op = Operation(FockOperationType.PhaseShift, phi=phi)
                signal.payload.fock.apply_operation(ps_op)
                self.send(self.Ports.output, signal)
