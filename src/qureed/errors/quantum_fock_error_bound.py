import logging
from dataclasses import dataclass
from typing import Any, Optional, Sequence

from qureed.logging.loggers import LoggerCategory
from qureed.simulation.simulation import Simulation
from .generic_error import GenericError


@dataclass
class QuantumFockErrorBound(GenericError):
    r"""
    Quantum Fock Error Bound Estimator

    The `QuantumFockErrorBound` class computes simulation error bounds for
    Fock-space quantum channels based on truncated or intentionally omitted
    Kraus operator decompositions. It is backend-dispatchable and currently
    implements PhotonWeave-compatible logic via `_compute_errors_photon_weave`.

    This class supports two error metrics:
    1. **Trace-norm** (`.error`)
      Estimates how much population is lost due to omitted Kraus operators,
      including both truncation effects and undeclared transitions.

      Mathematically:
      ---------------
      Given a quantum channel represented by a complete Kraus decomposition
      :math:`\{C_i\}_{i=0}^{\infty}`, and a state :math:`\rho_A`, we define
      the *used* set :math:`C^{(1)}=\{C_0, \ldots, C_K\}` and an *omitted*
      set :math:`C^{(2)}=\{C_{K+1}, \ldots}`.

      The trace-norm error bound is:

      .. math::

        \epsilon = \Tr[(I - \sum_{i=0} C_i^\dagger C_i) \rho_A]

    2. **Entanglement Fidelity error** (`.entanglement_error`)
      Measures how well the implemented channel perserves the input state when
      it is part of a larger entangled system., assuming the input state
      :math:`\rho_A` is part of a larger purified state
      :math:`|\psi_{ABE}\rangle`

      Mathematically:
      ---------------
      Let :math:`\mathcal{C}` be the ideal channel and
      :math:`\hat{\mathcal{C}}` the simulated one (based on the truncated set
      of Kraus operators).

      The **entanglement fidelity** is defined as:

      .. math::

          F_e(\rho_A,\hat{\mathcal{C}}) = \langle \psi_{ABE} |
          (\hat{\mathcal{C}}) \otimes \mathrm{Id}_{BE}(\rho_{ABE}) | \psi_{ABE}
          \rangle

      It can be constructed without erplicitly constructing a purification
      using:

      .. math::

          F_e(\rho_A, \hat{\mathcal{C}}) = \sum_i
          \left|\Tr[C_i \rho_A]\right|^2

      where :math:`C_i` are the Kraus operators used in the simulation.

      The corresponding entanglement error is:

      .. math::
          \delta_e = 1 - F_e
      This value lower-bounds the worst-case fidelity of the channel when
      applied to any purification of :math:`\rho_A`. It satisfies:

      .. math::

          F((\mathcal{C} \otimes \mathrm{Id})(\rho_{ABE}),
            (\hat{\mathcal{C}} \otimes \mathrm{Id})(\rho_{ABE}))
           \geq F_e(\rho_A, \hat{\mathcal{C}})


    Attributes:
    -----------
    error : `Optional[float]`
        The estimated trace-norm upper bound on the deviation from the full
        channel.
    entanglement_error : `Optional[float]`
        The deviation :math:`1-F_e` from perfect entanglement fidelity.


    Backend Compatibility:
    ----------------------
    This class supports backend dispatching via `Simulation().backend`.
    Currently implemented:
    - `_compute_errors_photon_weave` (JAX-based backend)

    Example:
    --------
    >>> from qureed.errors import QuantumFockErrorBound
    >>> qerr = QuantumFockErrorBound()
    >>> qerr.compute(rho_A, used_kraus_ops, omitted_kraus_ops)
    >>> print(f"Trace-norm error ≤ {qerr.error:.3e}")
    >>> print(f"Entanglement fidelity ≥ {1 - qerr.entanglement_error:.6f}")
    """

    error: Optional[float] = None
    entanglement_error: Optional[float] = None

    def compute(
        self,
        rho: Any,
        kraus_ops: Sequence[Any],
    ):
        er_logger = logging.getLogger(LoggerCategory.ERROR.value[0])

        if self.error is not None:
            er_logger.error("The error is already computed, can not recompute")
            return
        method_name = f"_compute_errors_{Simulation().backend}"
        method = getattr(self, method_name, None)
        if method is None:
            er_logger.error(
                f"The error method is not implemented for the chosen backend {
                    Simulation().backend}"
            )
        else:
            method(rho, kraus_ops)

    def _compute_errors_photon_weave(
        self,
        rho: Any,
        kraus_ops: Sequence[Any],
    ):
        import jax.numpy as jnp

        d = rho.shape[0]

        S_used = jnp.zeros((d, d), dtype=rho.dtype)
        for C in kraus_ops:
            S_used += C.conj().T @ C

        Id = jnp.eye(d, dtype=rho.dtype)
        E_total = Id - S_used

        # Total trace-norm bound: declared omission + unknown residual
        self.error = float(jnp.trace(E_total @ rho).real)

        fe = sum(jnp.abs(jnp.trace(rho @ C)) ** 2 for C in kraus_ops)
        self.entanglement_error = float(1 - fe)
