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
    return np.conjugate(a(cutoff)).T


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
def displacement(r, phi, cutoff, dtype=np.complex128):
    r"""Calculates the matrix elements of the displacement gate using a recurrence
    relation.

    Args:
        r (float): displacement magnitude
        phi (float): displacement angle
        cutoff (int): Fock ladder cutoff
        dtype (data type): Specifies the data type used for the calculation

    Returns:
        array[complex]: matrix representing the displacement operation.
    """
    D = np.zeros((cutoff, cutoff), dtype=dtype)
    sqrt = np.sqrt(np.arange(cutoff, dtype=dtype))
    mu = np.array([r * np.exp(1j * phi), -r * np.exp(-1j * phi)])

    D[0, 0] = np.exp(-0.5 * r**2)
    for m in range(1, cutoff):
        D[m, 0] = mu[0] / sqrt[m] * D[m - 1, 0]

    for m in range(cutoff):
        for n in range(1, cutoff):
            D[m, n] = (
                mu[1] / sqrt[n] * D[m, n - 1] + sqrt[m] / sqrt[n] * D[m - 1, n - 1]
            )

    return D


def fock_probability(n, state):
    return np.abs(state[tuple(n)]) ** 2


def mean_photon_number(state):
    dm = np.outer(state, np.conjugate(state))
    probabilities = np.diagonal(dm)
    n = np.arange(len(state))
    return np.sum(n * probabilities).real


@njit
def squeezing(r, phi, cutoff, dtype=np.complex128):
    r"""Calculates the matrix elements of the squeezing gate using a recurrence
    relation.

    Args:
        r (float): squeezing magnitude
        phi (float): squeezing angle
        cutoff (int): Fock ladder cutoff
        dtype (data type): Specifies the data type used for the calculation

    Returns:
        array[complex]: matrix representing the squeezing gate.
    """
    S = np.zeros((cutoff, cutoff), dtype=dtype)
    sqrt = np.sqrt(np.arange(cutoff, dtype=dtype))

    eitheta_tanhr = np.exp(1j * phi) * np.tanh(r)
    sechr = 1.0 / np.cosh(r)
    R = np.array(
        [
            [-eitheta_tanhr, sechr],
            [sechr, np.conj(eitheta_tanhr)],
        ]
    )

    S[0, 0] = np.sqrt(sechr)
    for m in range(2, cutoff, 2):
        S[m, 0] = sqrt[m - 1] / sqrt[m] * R[0, 0] * S[m - 2, 0]

    for m in range(0, cutoff):
        for n in range(1, cutoff):
            if (m + n) % 2 == 0:
                S[m, n] = (
                    sqrt[n - 1] / sqrt[n] * R[1, 1] * S[m, n - 2]
                    + sqrt[m] / sqrt[n] * R[0, 1] * S[m - 1, n - 1]
                )
    return S


@njit
def kerr(k, cutoff):
    n = np.arange(cutoff)
    ret = np.diag(np.exp(1j * k * n**2))
    return ret


@njit
def calculate_fidelity(state_1, state_2):

    if state_1.ndim == 2 and state_2.ndim == 2:
        return np.abs(np.sum(np.sqrt(np.linalg.eigvals(state_1 @ state_2)))) ** 2

    elif state_1.ndim == 1 and state_2.ndim == 2:
        return (np.conjugate(state_1) @ state_2 @ state_1).real

    elif state_1.ndim == 1 and state_2.ndim == 1:
        return np.abs(np.dot(np.conjugate(state_1), state_2)) ** 2
    else:
        return (np.conjugate(state_2) @ state_1 @ state_2).real
