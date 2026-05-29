import jax.numpy as jnp


def generate_polarization_phase_operator(phase: float) -> jnp.ndarray:
    """
    Construct a unitary 2×2 operator that applies a relative phase to the
    vertical polarization (|V⟩) component while leaving the horizontal (|H⟩)
    component unchanged.

    Specifically, this operator acts on the polarization basis ``{|H⟩, |V⟩}``
    as:

    .. math::

        U(\\phi) =
        \\begin{bmatrix}
            1 & 0 \\\\
            0 & e^{i\\phi}
        \\end{bmatrix}

    where :math:`\\phi` is the provided phase angle in radians.

    Parameters
    ----------
    phase : float
        Phase angle :math:`\\phi` to apply to the vertical polarization
        component.

    Returns
    -------
    jnp.ndarray
        A 2×2 complex-valued unitary matrix implementing the phase shift on
        |V⟩.
    """
    return jnp.array(
        [[1.0, 0.0], [0.0, jnp.exp(1j * phase)]], dtype=jnp.complex64
    )
