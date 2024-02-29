import string
from itertools import chain, product

import numpy as np
from numba import njit, prange
from scipy.linalg import expm as matrixExp
from scipy.special import factorial
from quasi._math.states import FockState

r"""
The functions implemented here is derived from this paper:
https://arxiv.org/pdf/2004.11002.pdf

"""


def_type = np.complex128
indices = string.ascii_lowercase


def genOfRange(size):
    """
    Converts a range into a generator.
    """
    for i in range(size):
        yield i


def genOfTuple(t):
    """
    Converts a tuple into a generator
    """
    for val in t:
        yield val


def indexRange(lst, trunc):
    """
    Returns a generator ranging over the possible values for unspecified
    indices in `lst`.

    Example:
        .. code-block:: python

                >>> for i in indexRange([0, None, 1, None], 3): print i
                (0, 0, 1, 0)
                (0, 0, 1, 1)
                (0, 0, 1, 2)
                (0, 1, 1, 0)
                (0, 1, 1, 1)
                (0, 1, 1, 2)
                (0, 2, 1, 0)
                (0, 2, 1, 1)
                (0, 2, 1, 2)

    Args:
        lst (list<int or None>): a list of (possible unspecified) integers
        trunc (int): the number to range unspecified values up to

    Returns:
        Generator of ints
    """

    for vals in product(*([range(trunc) for x in lst if x is None])):
        gen = genOfTuple(vals)
        yield [
            next(gen) if v is None else v for v in lst
        ]  # pylint: disable=stop-iteration-return


def index(lst, trunc):
    """
    Converts an n-ary index to a 1-dimensional index.
    """
    return sum([lst[i] * trunc ** (len(lst) - i - 1) for i in range(len(lst))])


def unIndex(i, n, trunc):
    """
    Converts a 1-dimensional index ``i`` with truncation ``trunc`` and
    number of modes ``n`` to a n-ary index.
    """
    return [i // trunc ** (n - 1 - m) % trunc for m in range(n)]


def sliceExp(axes, ind, n):
    """
    Generates a slice expression for a list of pairs of axes (modes) and indices.
    """
    return [ind[i] if i in axes else slice(None, None, None) for i in range(n)]


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
def fock_operator(n, cut):
    op = adagger(cut)
    for _ in prange(n):
        op = op @ op
    return op

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
    return np.array(
        [1.0 + 0.0j if i == n else 0.0 + 0.0j for i in range(cutoff)]
    )


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
                mu[1] / sqrt[n] * D[m, n - 1]
                + sqrt[m] / sqrt[n] * D[m - 1, n - 1]
            )

    return D


def fock_probability(n, state):
    return np.abs(state[tuple(n)]) ** 2


def mean_photon(state, mode,):
    # pylint: disable=unused-argument
    n = np.arange(state._cutoff)
    probs = np.diagonal(state.reduced_dm(mode))
    return np.sum(n*probs).real


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
        return (
            np.abs(np.sum(np.sqrt(np.linalg.eigvals(state_1 @ state_2)))) ** 2
        )

    elif state_1.ndim == 1 and state_2.ndim == 2:
        return (np.conjugate(state_1) @ state_2 @ state_1).real

    elif state_1.ndim == 1 and state_2.ndim == 1:
        return np.abs(np.dot(np.conjugate(state_1), state_2)) ** 2
    else:
        return (np.conjugate(state_2) @ state_1 @ state_2).real


def apply_gate_einsum(mat, state, modes, n):
    """
    Gate application based on einsum.
    Assumes the input matrix has shape (out1, in1, ...)
    """
    # pylint: disable=unused-argument

    size = len(modes)

    if n == 1:
        return np.dot(mat, np.dot(state, mat.conj().T))

    in_str = indices[: n * 2]

    j = genOfRange(n * 2)
    out_str = "".join(
        [
            indices[n * 2 + next(j)] if i // 2 in modes else indices[i]
            for i in range(n * 2)
        ]
    )

    j = genOfRange(size * 2)
    left_str = "".join(
        [
            out_str[modes[i // 2] * 2]
            if (i % 2) == 0
            else in_str[modes[i // 2] * 2]
            for i in range(size * 2)
        ]
    )
    right_str = "".join(
        [
            out_str[modes[i // 2] * 2 + 1]
            if (i % 2) == 0
            else in_str[modes[i // 2] * 2 + 1]
            for i in range(size * 2)
        ]
    )

    einstring = "".join([left_str, ",", in_str, ",", right_str, "->", out_str])
    return np.einsum(einstring, mat, state, mat.conj())


def apply_gate_BLAS(mat, state, modes, n, trunc):
    """
    Gate application based on custom indexing and matrix multiplication.
    Assumes the input matrix has shape (out1, in1, ...).

    This implementation uses indexing and BLAS. As per stack overflow,
    einsum doesn't actually use BLAS but rather a c implementation. In theory
    if reshaping is efficient this should be faster.
    """

    size = len(modes)
    dim = trunc**size
    stshape = [trunc for i in range(size)]

    # Apply the following matrix transposition:
    # |m1><m1| |m2><m2| ... |mn><mn| -> |m1>|m2>...|mn><m1|<m2|...<mn|
    transpose_list = [2 * i for i in range(size)] + [
        2 * i + 1 for i in range(size)
    ]
    matview = np.transpose(mat, transpose_list).reshape((dim, dim))

    if n == 1:
        return np.dot(mat, np.dot(state, mat.conj().T))

    # Transpose the state into the following form:
    # |psi><psi||mode[0]>|mode[1]>...|mode[n]><mode[0]|<mode[1]|...<mode[n]|
    transpose_list = [i for i in range(n * 2) if not i // 2 in modes]
    transpose_list = (
        transpose_list + [2 * i for i in modes] + [2 * i + 1 for i in modes]
    )
    view = np.transpose(state, transpose_list)

    # Apply matrix to each substate
    ret = np.zeros([trunc for i in range(n * 2)], dtype=def_type)
    for i in product(*([range(trunc) for j in range((n - size) * 2)])):
        ret[i] = np.dot(
            matview, np.dot(view[i].reshape((dim, dim)), matview.conj().T)
        ).reshape(stshape + stshape)

    # "untranspose" the return matrix ret
    untranspose_list = [0] * len(transpose_list)
    for i in range(len(transpose_list)):
        untranspose_list[transpose_list[i]] = i

    return np.transpose(ret, untranspose_list)


def proj(i, j, trunc):
    r"""
    The projector :math:`P = \ket{j}\bra{i}`.
    """
    P = np.zeros((trunc, trunc), dtype=def_type)
    P[j][i] = 1.0 + 0.0j
    return P


def lossChannel(T, trunc):
    r"""
    The Kraus operators for the loss channel :math:`\mathcal{N}(T)`.
    """

    TToAdaggerA = np.array(
        np.diag([T ** (i / 2) for i in range(trunc)]), dtype=def_type
    )

    def aToN(n):
        """the nth matrix power of the annihilation operator matrix a"""
        return np.linalg.matrix_power(a(trunc), n)

    def E(n):
        """the loss channel amplitudes in the Fock basis"""
        return ((1 - T) / T) ** (n / 2) * np.dot(
            aToN(n) / np.sqrt(factorial(n)), TToAdaggerA
        )

    if T == 0:
        return [proj(i, 0, trunc) for i in range(trunc)]

    return [E(n) for n in range(trunc)]


def reduced_dm(state, modes, ):

    keep_indices = indices[: 2 * len(modes)]
    trace_indices = indices[2 * len(modes) : len(modes) + state._modes]

    ind = [i * 2 for i in trace_indices]
    ctr = 0

    for m in range(state._modes):
        if m in modes:
            ind.insert(m, keep_indices[2 * ctr : 2 * (ctr + 1)])
            ctr += 1

    indStr = "".join(ind) + "->" + keep_indices
    return np.einsum(indStr, state.dm())


def homodyne(state, phi, mode, hbar):
    anni = a(state._modes)
    create = adagger(state._cutoff)

    x = np.sqrt(hbar / 2) * (anni + create)
    p = -1j * np.sqrt(hbar / 2) * (anni - create)

    xphi = np.cos(phi) * x + np.sin(phi) * p

    rho = reduced_dm(state, mode)

    return np.trace(np.dot(xphi, rho)).real


def calculate_trace(state):
    eqn_indices = [[indices[idx]] * 2 for idx in range(state._num_modes)]
    eqn = "".join(chain.from_iterable(eqn_indices))
    return np.einsum(eqn, state.dm()).real


def partial_trace(state, n, modes):
    """
    Computes the partial trace of a state over the modes in `modes`.

    Expects state to be in mixed state form.
    """
    left_str = [
        indices[2 * i] + indices[2 * i]
        if i in modes
        else indices[2 * i : 2 * i + 2]
        for i in range(n)
    ]
    out_str = [
        "" if i in modes else indices[2 * i : 2 * i + 2] for i in range(n)
    ]
    einstr = "".join(left_str + ["->"] + out_str)

    return np.einsum(einstr, state)


def vacuumStateMixed(n, trunc):
    r"""
    The `n`-mode mixed vacuum state :math:`\ket{00\dots 0}\bra{00\dots 0}`
    """

    state = np.zeros([trunc for i in range(n * 2)], dtype=def_type)
    state.ravel()[0] = 1.0 + 0.0j
    return state


def thermalState(nbar, trunc):
    r"""
    The thermal state :math:`\rho(\overline{nbar})`.
    """
    if nbar == 0:
        st = fock_state(0, trunc)
        state = np.outer(st, st.conjugate())
    else:
        coeff = np.array(
            [nbar**n / (nbar + 1) ** (n + 1) for n in range(trunc)]
        )
        state = np.diag(coeff)

    return state


def cubicPhase(gamma, hbar, trunc):
    r"""
    The cubic phase gate :math:`\exp{(i\frac{\gamma}{3\hbar}\hat{x}^3)}`.
    """
    a_ = a(trunc)
    x = (a_ + np.conj(a_).T) * np.sqrt(hbar / 2)
    x3 = x @ x @ x
    ret = matrixExp(1j * gamma / (3 * hbar) * x3)
    return ret


def apply_channel(state: FockState, kraus_ops, modes):
    """Master channel application function. Applies a channel represented by
    Kraus operators.

    .. note::
            Always results in a mixed state.

    Args:
        kraus_ops (list<array>): A list of Kraus operators
        modes (list<non-negative int>): The modes to apply the channel to
    """

    states = [
        apply_gate_einsum(k, state, modes, state._num_modes) for k in kraus_ops
    ]
    return sum(states)


def norm(state: FockState):
    """returns the norm of the state"""
    return calculate_trace(state)


def tensor(u, v, n, pos=None):
    """
    Returns the tensor product of `u` and `v`, optionally spliced into a
    at location `pos`.
    """

    w = np.tensordot(u, v, axes=0)

    if pos is not None:
        scale = 2
        for i in range(v.ndim):
            w = np.rollaxis(w, scale * n + i, scale * pos + i)

    return w


def mix(state, n):
    """
    Transforms a pure state into a mixed state. Does not do any checks on the
    shape of the input state.
    """

    left_str = [indices[i] for i in range(0, 2 * n, 2)]
    right_str = [indices[i] for i in range(1, 2 * n, 2)]
    out_str = [indices[: 2 * n]]
    einstr = "".join(left_str + [","] + right_str + ["->"] + out_str)
    return np.einsum(einstr, state, state.conj())