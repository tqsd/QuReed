from typing import Tuple, Dict, Callable
import jax.numpy as jnp


def generate_entangling_operator() -> (
    Tuple[Tuple, Dict[str, Callable[[Tuple[int, ...]], jnp.ndarray]]]
):
    """
    Generate a symbolic operator and its context to create a
    polarization-entangled two-photon state across four Fock modes.

    The operator is expressed symbolically using nested tuples, to be
    interpreted by the PhotonWeave backend. The associated context provides
    callable functions to generate the corresponding operator matrices for
    specific mode dimensions.

    Four creation modes are assumed:
        - mode 0 with horizontal (H) and vertical (V) polarizations
        - mode 1 with horizontal (H) and vertical (V) polarizations

    That is:
        - ``mode0_H, mode0_V, mode1_H, mode1_V``

    The constructed operator corresponds to the following entangled state:

    .. math::

        \\frac{1}{\\sqrt{2}} \\left( a_{0H}^\\dagger a_{1H}^\\dagger
        + a_{0V}^\\dagger a_{1V}^\\dagger \\right) |\\text{vac}\\rangle

    Which, when applied to vacuum, results in the Bell-like state:

    .. math::

        \\frac{1}{\\sqrt{2}} \\left(
            |1\\rangle_{0H} |1\\rangle_{1H} |0\\rangle_{0V} |0\\rangle_{1V}
            + |0\\rangle_{0H} |0\\rangle_{1H} |1\\rangle_{0V} |1\\rangle_{1V}
        \\right)

    Returns
    -------
    Tuple[Tuple, Dict[str, Callable[[Tuple[int, ...]], jnp.ndarray]]]
        A tuple containing:
        - The symbolic operator expression as a nested tuple
        - A context dictionary mapping symbolic node names (str) to
          functions that construct matrix representations based on mode
          dimensions
    """

    def identity(dim):
        return jnp.eye(dim)

    def c(dim):
        return jnp.diag(jnp.ones(dim - 1, dtype=jnp.complex64), k=-1)

    entangling_operation = (
        "s_mult",
        1 / jnp.sqrt(2),
        (
            "add",
            ("kron", "c0H", "I0V", "c1H", "I1V"),
            ("kron", "I0H", "c0V", "I1H", "c1V"),
        ),
    )

    entangling_operation_context = {
        "c0H": lambda dims: c(dims[0]),
        "I0H": lambda dims: identity(dims[0]),
        "c0V": lambda dims: c(dims[1]),
        "I0V": lambda dims: identity(dims[1]),
        "c1H": lambda dims: c(dims[2]),
        "I1H": lambda dims: identity(dims[2]),
        "c1V": lambda dims: c(dims[3]),
        "I1V": lambda dims: identity(dims[3]),
    }

    return entangling_operation, entangling_operation_context
