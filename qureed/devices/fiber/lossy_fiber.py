from typing import Dict, Any, cast
from examples.BB84.custom_fiber import QuantumOpticalPulseSignal
from qureed.constants import C0
from qureed.devices.fiber.generic_fiber import GenericFiber
from qureed.devices.wrappers import des_proc
from qureed.errors.generic_fock_error_bound import QuantumFockErrorBound
from qureed.signals.quantum_optical_pulse_signal import QOPSignalType
from qureed.simulation.simulation import Simulation


class LossyFiber(GenericFiber):
    r"""
    Lossy Fiber Device

    An optical *single-mode* fiber segment that introduces both **temporal
    delay** and **photon-number attenuation** to traversing quantum optical
    pulses. The component is passive and fully described by its physical
    parameters (`length`, `n`, `loss`).

    Ports
    -----
    - input (input)  : Accepts a `QuantumOpticalPulseSignal`
    - output (outpu) : Emits attenuated and delayed `QuantumOpticalPulseSignal`

    Properties:
    -----------
    - length : `float`
        Physical fiber length *L* in meters.
    loss : float
        Linear attenuation coefficient :math:`\alpha \;[\text{m}^{-1}]`.
        The *power* transmission is given by
    n : float
        Effective group refractive index :math:`n` (determines propagation
        speed).

    Backend Compatibility
    ---------------------
    * **photon_weave** – uses ``_attenuate_photon_weave`` which constructs a
      Kraus representation of the lossy bosonic channel and attaches a
      :class:`QuantumFockErrorBound` object describing the incurred truncation
      error.
    * **other backends** – must implement ``_attenuate_<backend>()`` following
      the naming convention.  A :class:`NotImplementedError` is raised if the
      method is missing.
    """

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

        Raises:
        -------
        NotImplementedError
            If the current bacend does **not** implement the expected helper
            function.
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
        """
        Main device coroutine (backend-agnotic)

        The process simply introduces a *propagation delay* of
        ``length / (c0 / n)`` and subsequently applies the backend-specific
        attenuation when *END*0marker of the pulse arrives. The *START*
        marker is forwarded immediately (after delay) so that downstream
        components can allocate resources while the quantum state is still
        travelling.
        """
        length = self.get_property("length")
        n = self.get_property("n")
        v = C0 / n
        self.delay = length / v
        while True:
            signal = yield self.receive(self.Ports.input)
            if signal.type is QOPSignalType.START:
                self._send_with_delay(self.Ports.output, signal)
                continue
            self._attenuate(signal)
            self._send_with_delay(self.Ports.output, signal)

    def _compute_attenuation_channel_pw(self, d: int):
        r"""
        Returns Kraus operators of the lossy bosonic channel (dimension *d*).

        The loss channel is expressed as a set of *d* Kraus operators
        :math:`\{C_k\}` where

        .. math::

            C_k = \sum_{n=k}^{d-1}\sqrt{\binom{n}{k}\,\eta^{\,n-k}\,(1-\eta)^k}
                    |n-k\rangle\langle n|.

        with :math:`\eta = e^{-\alpha L}`.  The implementation follows
        *Scarani, Finite‑dimensional bosonic channels* (2013) and uses JAX for
        efficient array construction.

        Parameters
        ----------
        d : int
            Cut‑off dimension of the truncated Fock space.

        Returns
        -------
        list[ArrayLike]
            A list of *d* complex‑valued Kraus matrices of shape ``(d, d)``.
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
        from photon_weave.state.envelope import Envelope

        env = cast(Envelope, signal.payload)

        loss_channel = self._compute_attenuation_channel_pw(
            env.fock.dimensions
        )
        # Ensure that we have density matrix
        env.fock.expand()
        env.fock.expand()

        rho = env.fock.trace_out()
        err = QuantumFockErrorBound()
        err.compute(rho, loss_channel)
        err.description = "Error due to lossy fiber"

        env.fock.apply_kraus(loss_channel, identity_check=False)

        signal.errors.append(err)
