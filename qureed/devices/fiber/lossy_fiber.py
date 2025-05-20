from typing import Dict, Any
from examples.BB84.custom_fiber import QuantumOpticalPulseSignal
from qureed.constants import C0
from qureed.devices.fiber.generic_fiber import GenericFiber
from qureed.devices.wrappers import des_proc
from qureed.errors.generic_fock_error_bound import QuantumFockErrorBound
from qureed.signals.quantum_optical_pulse_signal import QOPSignalType
from qureed.simulation.simulation import Simulation


class LossyFiber(GenericFiber):

    properties: Dict[str, Dict[str, Any]] = {
        "length": {"type": float, "value": 100},  # meters
        "loss": {"type": float, "value": 4.6e-5},  # per-meter attenuation
        "n": {"type": float, "value": 1.45},  # refractive index
    }

    @property
    def gui_name(self) -> str:
        return "Lossy Fiber"

    def _attenuate(self, signal: QuantumOpticalPulseSignal) -> None:
        """
        Dispatches signal attenuation to the backend-specific implementation.

        This is used to attenuate the signal according to the `length` and
        `loss` property. The backend-specific method is determined by the
        currently active simulation backend.

        Arguments:
        ----------
        signal: `QuantumOpticalPulseSignal`
            The signal to attenuate
        """
        method_name = f"_attenuate_{Simulation().backend}"
        method = getattr(self, method_name, None)
        if method is None:
            raise NotImplementedError(
                "_attenuate method not implemented for backend "
                f"{Simulation().backend}; expected method {method_name}"
            )
        return method(signal)

    @des_proc
    def proc(self):
        length = self.get_property("length")
        n = self.get_property("n")
        v = C0 / n
        self.delay = length / v
        while True:
            signal = yield self.receive(self.Ports.input)
            if signal.type is QOPSignalType.START:
                self._send_with_delay(signal)
                continue
            self._attenuate(signal)
            self._send_with_delay(signal)

    def _compute_attenuation_channel_pw(self, d: int):
        """
        Computes the attenuation channel
        """
        import jax.numpy as jnp
        from jax.scipy.special import gammaln

        def binom(n, k):
            return jnp.exp(
                gammaln(n + 1) - gammaln(k + 1) - gammaln(n - k + 1)
            )

        L = self.get_property("length")
        alpha = self.get_property("loss")
        eta = jnp.exp(-alpha * L)

        C_ops = []
        # Build each C_k as a (d x d) complex array
        for k in range(d):
            Ck = jnp.zeros((d, d), dtype=jnp.complex64)
            n = jnp.arange(k, d)
            coeff = jnp.sqrt(
                binom(n, k) * jnp.power(eta, n - k) * jnp.power(1 - eta, k)
            )
            Ck = Ck.at[(n - k, n)].set(coeff)
            C_ops.append(Ck)
        return C_ops

    def _attenuate_photon_weave(
        self, signal: QuantumOpticalPulseSignal
    ) -> None:
        """
        Attenuate Signal for the photon_weave backend.

        Creates the Channel using Kraus representation applies the channel to
        the given space and computes the error bound.

        Arguments:
        ----------
        signal: `QuantumOpticalPulseSignal`
            The signal to attenuate
        """
        loss_channel = self._compute_attenuation_channel_pw(
            signal.payload.fock.dimensions
        )
        # Ensure that we have density matrix
        signal.payload.fock.expand()
        signal.payload.fock.expand()

        rho = signal.payload.fock.trace_out()
        err = QuantumFockErrorBound()
        err.compute(rho, loss_channel)
        signal.payload.fock.apply_kraus(loss_channel, identity_check=False)
        signal.errors.append(err)
