import abc
import string
from itertools import chain
from copy import copy
from .ops import calculate_trace
import numpy as np


indices = string.ascii_lowercase


class State(abc.ABC):
    r"""Abstract base class for the representation of quantum states."""

    def __init__(self, num_modes, hbar=2):
        self._num_modes = num_modes
        self._hbar = hbar
        self._data = None


class FockState(State):
    r"""Class for the representation of quantum states in the Fock basis.

    Args:
        state_data (array): the state representation in the Fock basis
        num_modes (int): the number of modes in the state
        pure (bool): True if the state is a pure state, false if the state is mixed
        cutoff_dim (int): the Fock basis truncation size
        hbar (float): (default 2) The value of :math:`\hbar` in the definition of :math:`\x` and :math:`\p` (see :ref:`opcon`)
        mode_names (Sequence): (optional) this argument contains a list providing mode names
            for each mode in the state
    """

    def __init__(self, state_data, num_modes, cutoff_dim, hbar=2):
        # pylint: disable=too-many-arguments

        super().__init__(num_modes, hbar)

        self._data = state_data
        self._cutoff = cutoff_dim
        self._basis = "fock"

    @property
    def cutoff_dim(self):
        r"""The numerical truncation of the Fock space used by the underlying state.
        Note that a cutoff of D corresponds to the Fock states :math:`\{|0\rangle,\dots,|D-1\rangle\}`

        Returns:
            int: the cutoff dimension
        """
        return self._cutoff

    def dm(self) -> np.ndarray:
        return self._data

    def trace(self, **kwargs):
        r"""Trace of the density operator corresponding to the state.


        For physical states this should always be 1, any deviations from this value are due
        to numerical errors and Hilbert space truncation artefacts.

        Returns:
          float: trace of the state
        """
        return calculate_trace(self.dm())

    def all_fock_probs(self):
        r"""Probabilities of all possible Fock basis states for the current circuit state.

        For example, in the case of 3 modes, this method allows the Fock state probability
        :math:`|\braketD{0,2,3}{\psi}|^2` to be returned via

        .. code-block:: python

            probs = state.all_fock_probs()
            probs[0,2,3]

        Returns:
            array: array of dimension :math:`\underbrace{D\times D\times D\cdots\times D}_{\text{num modes}}`
                containing the Fock state probabilities, where :math:`D` is the Fock basis cutoff truncation
        """

        dm = self.dm()
        num_axes = len(dm.shape)
        evens = [k for k in range(0, num_axes, 2)]
        odds = [k for k in range(1, num_axes, 2)]
        flat_size = np.prod([dm.shape[k] for k in range(0, num_axes, 2)])
        transpose_list = evens + odds
        probs = np.diag(
            np.reshape(
                np.transpose(dm, transpose_list), [flat_size, flat_size]
            )
        ).real

        return np.reshape(probs, [self._cutoff] * self._num_modes)
