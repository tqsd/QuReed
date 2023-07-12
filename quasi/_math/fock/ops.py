import numpy as np
from numba import njit
from scipy.special import factorial

r"""
The functions implemented here is derived from this paper:
https://arxiv.org/pdf/2004.11002.pdfs

"""


@njit
def a(cutoff):
    r"""
    The annihilation operator :math:`a`.
    """
    data = np.sqrt(np.arange(1, cutoff, dtype=np.complex128))

    return np.diag(data, 1)


@njit
def adagger(cutoff):
    r"""
    The creation operator :math:`a^\dagger`
    """
    return a(cutoff).conj().T


@njit
def beamsplitter(theta, phi, cutoff, dtype=np.complex128):

    sqrt_values = np.sqrt(np.arange(cutoff, dtype=dtype))
    cos_theta = np.cos(theta)
    sin_theta_complex = np.sin(theta) * np.exp(1j * phi)

    V = np.array(
        [
            [0, 0, cos_theta, -np.conj(sin_theta_complex)],
            [0, 0, sin_theta_complex, cos_theta],
            [cos_theta, sin_theta_complex, 0, 0],
            [-np.conj(sin_theta_complex), cos_theta, 0, 0],
        ]
    )

    B = np.zeros((cutoff, cutoff, cutoff, cutoff), dtype=dtype)
    B[0, 0, 0, 0] = 1.0  # equation 73

    for m in range(cutoff):  # equation 74
        for n in range(cutoff - m):
            p = m + n
            if 0 < p < cutoff:
                B[m, n, p, 0] = (1 / sqrt_values[p]) * (
                    V[0, 2] * sqrt_values[m] * B[m - 1, n, p - 1, 0]
                    + V[1, 2] * sqrt_values[n] * B[m, n - 1, p - 1, 0]
                )

    for m in range(cutoff):  # equation 75
        for n in range(cutoff):
            for p in range(cutoff):
                q = m + n - p
                if 0 < q < cutoff:
                    B[m, n, p, q] = (1 / sqrt_values[q]) * (
                        V[0, 3] * sqrt_values[m] * B[m - 1, n, p, q - 1]
                        + V[1, 3] * sqrt_values[n] * B[m, n - 1, p, q - 1]
                    )
    return B


def phase(theta, cutoff):

    return np.array(np.diag([np.exp(1j * n * theta) for n in range(cutoff)]))


def vacuum_state(n, cutoff):

    state = np.zeros([cutoff for i in range(n)], dtype=np.complex128)
    state.ravel()[0] = 1.0 + 0.0j
    return state


@njit
def fock_state(n, cutoff):

    return np.array([1.0 + 0.0j if i == n else 0.0 + 0.0j for i in range(cutoff)])


def coherent_state(r, phi, cutoff):
    alpha = r * np.exp(1j * phi)
    normalization = np.exp(-(alpha.real**2 + alpha.imag**2) / 2)

    return normalization * np.array(
        [alpha**n / np.sqrt(factorial(n)) for n in range(cutoff)]
    )


@njit
def displacment(
    r,
    phi,
    cutoff,
):

    sqrt_values = np.sqrt(np.arange(cutoff, dtype=np.complex128))
    alpha = r * np.exp(1j * phi)
    D = np.zeros((cutoff, cutoff), dtype=np.complex128)
    D[0, 0] = np.exp(-(r**2) / 2)  # equation 56

    for row in range(1, cutoff):  # equation 57
        D[row, 0] = alpha / sqrt_values[row] * D[row - 1, 0]

    for row in range(cutoff):  # equation 58
        for col in range(1, cutoff):
            D[row, col] = (-np.conj(alpha) / sqrt_values[col] * D[row, col - 1]) + (
                sqrt_values[row] / sqrt_values[col] * D[row - 1, col - 1]
            )

    return D


def fock_probability(n, state):
    return np.abs(state[tuple(n)]) ** 2


def mean_photon_number(state):
    dm = np.outer(state, state.conj())
    probabilities = np.diagonal(dm)
    n = np.arange(len(state))
    return np.sum(n * probabilities).real


@njit
def squeezing(r, theta, cutoff):

    S = np.zeros((cutoff, cutoff), dtype=np.complex128)

    sqrt_values = np.sqrt(np.arange(cutoff, dtype=np.complex128))
    sech_r = 1.0 / np.cosh(r)
    tanh_r_complex = np.exp(1j * theta) * np.tanh(r)

    S[0, 0] = sech_r**0.5

    for m in range(2, cutoff, 2):
        S[m, 0] = sqrt_values[m - 1] / sqrt_values[m] * -tanh_r_complex * S[m - 2, 0]

    for m in range(0, cutoff):
        for n in range(1, cutoff):
            if (m + n) % 2 == 0:
                S[m, n] = (1 / sqrt_values[n]) * (
                    sqrt_values[m] * sech_r * S[m - 1, n - 1]
                    + sqrt_values[n - 1] * tanh_r_complex.conj() * S[m, n - 2]
                )
    return S
