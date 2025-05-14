from typing import Dict, Tuple, Union, Any, cast

from qureed.simulation.simulation import Simulation
from .generic_beam_splitter import GenericBeamSplitterDevice
from qureed.devices.wrappers import des_proc
from qureed.signals import QuantumOpticalPulseSignal, QOPSignalType


class PerfectOverlapBeamSplitter(GenericBeamSplitterDevice):

    def __init__(self, uid=None, **kwargs):
        super().__init__(uid, **kwargs)
        self._buffer: list[Dict[str, Any]] = []
        self.delay = 1.5e-10

    @property
    def gui_name(self) -> str:
        return "Perfect Overlap Beam Splitter"

    def _port_translation(
        self, port: Union[str, GenericBeamSplitterDevice.Ports]
    ) -> GenericBeamSplitterDevice.Ports:
        if port == self.Ports.A:
            return self.Ports.C
        return self.Ports.D

    def _store_and_send_starts(
        self,
        starts: Dict[
            float,
            Dict[GenericBeamSplitterDevice.Ports, QuantumOpticalPulseSignal],
        ],
    ) -> None:
        for wl, signals in starts.items():
            entry = {
                "wl": wl,
                "starts": signals,
                "ends": {},
                "ts": self.sim_env.now,
            }
            self._buffer.append(entry)
            for port, signal in signals.items():
                self.send(self._port_translation(port), signal)

    def _generate_signals(
        self, signal: QuantumOpticalPulseSignal
    ) -> Tuple[QuantumOpticalPulseSignal, QuantumOpticalPulseSignal]:
        method_name = f"_generate_signals_{Simulation().backend}"
        method = getattr(self, method_name, None)
        if method is None:
            raise NotImplementedError(
                "_generate_starts method not implemented for backend "
                f"{Simulation().backend}; expected method {method_name}"
            )
        return method(signal)

    def _mixing_process(
        self,
        signal_1: QuantumOpticalPulseSignal,
        signal_2: QuantumOpticalPulseSignal,
    ):
        method_name = f"_mixing_process_{Simulation().backend}"
        method = getattr(self, method_name, None)
        if method is None:
            raise NotImplementedError(
                "_process_mixing method not implemented for backend "
                f"{Simulation().backend}; expected method {method_name}"
            )
        return method(signal_1, signal_2)

    def _send_with_delay(self, port, signal):
        def __send():
            yield self.sim_env.timeout(self.delay)
            self.send(port, signal)

        self.sim_env.process(__send())

    @des_proc
    def proc_pw(self):
        while True:
            received = yield from self.any_receive(self.Ports.A, self.Ports.B)
            to_send = []

            starts: Dict[
                float,
                Dict[
                    GenericBeamSplitterDevice.Ports, QuantumOpticalPulseSignal
                ],
            ] = {}
            for signal, port in received:
                if signal.type is QOPSignalType.START:
                    wl = signal.metadata.get("central_wavelenght", -1)
                    bucket = starts.setdefault(wl, {})
                    bucket[port] = signal

            for wl, signals in starts.items():
                if len(signals) == 1:
                    # Maybe this part can be backend specific
                    existing_port = next(iter(signals.keys()))
                    other_port = (
                        self.Ports.B
                        if existing_port is self.Ports.A
                        else self.Ports.A
                    )

                    start_signal, _ = self._generate_signals(
                        signals[existing_port]
                    )

                    starts[wl][other_port] = start_signal

            if starts:
                self._store_and_send_starts(starts)

            for signal, port in received:
                if signal.type is QOPSignalType.END:
                    wl = signal.metadata.get("central_wavelenght", -1)
                    matching_start = signal.pair

                    bucket = next(
                        e
                        for e in self._buffer
                        if e["wl"] == wl
                        and matching_start in e["starts"].values()
                    )
                    bucket["ends"][port] = signal
                    if bucket not in to_send:
                        to_send.append(bucket)

            # Mix all the signals in the to_send set
            for entry in to_send:
                if set(entry["ends"].keys()) == {self.Ports.A, self.Ports.B}:
                    sigA = entry["starts"][self.Ports.A]
                    sigB = entry["starts"][self.Ports.B]

                    out_C, out_D = self._mixing_process(sigA, sigB)

                    self._send_with_delay(self.Ports.C, out_C)
                    self._send_with_delay(self.Ports.D, out_D)

                    self._buffer.remove(entry)

    # <<< PHOTON WEAVE SPECIFIC METHODS >>>

    def _generate_signals_photon_weave(
        self, signal
    ) -> Tuple[QuantumOpticalPulseSignal, QuantumOpticalPulseSignal]:
        from photon_weave.state.envelope import Envelope

        new_envelope = Envelope()
        return QuantumOpticalPulseSignal.create_pair(
            payload=new_envelope,
            metadata=signal.metadata,
        )

    def _mixing_process_photon_weave(
        self,
        signal_1: QuantumOpticalPulseSignal,
        signal_2: QuantumOpticalPulseSignal,
    ):
        from photon_weave.state.envelope import Envelope
        from photon_weave.state.composite_envelope import CompositeEnvelope
        from photon_weave.operation import Operation, CompositeOperationType

        envelope_1 = cast(Envelope, signal_1.payload)
        envelope_2 = cast(Envelope, signal_2.payload)

        ce = CompositeEnvelope(envelope_1, envelope_2)

        op = Operation(
            CompositeOperationType.NonPolarizingBeamSplitter,
            eta=self.get_property("eta"),
        )
        ce.apply_operation(op, envelope_1.fock, envelope_2.fock)
