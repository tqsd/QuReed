from quasi._math.states import FockState
from quasi._math.fock import ops

import numpy as np


class Experiement:
    """Singleton object"""

    def __init__(self, num_modes, hbar=2, cutoff=10):
        """
        Initialization method
        """
        self.data = None
        self.init_modes = 1
        self.cutoff = cutoff
        self.num_modes = num_modes
        self.hbar = hbar
        self.state_preparations: list = []
        self.operations: list = []
        self.channels: list = []

    def add_operation(self, operator, modes):
        self.operations.append((operator, modes))

    def prepare_experiment(self):
        ground_state = ops.vacuumStateMixed(self.num_modes, trunc=self.cutoff)
        self.state = FockState(
            ground_state,
            self.num_modes,
            cutoff_dim=self.cutoff,
            hbar=self.hbar,
        )
        return self.state

    def prepare_multimode(self, data, modes):
        r"""
        Prepares a given mode or list of modes in the given state.

        Args:
            state (array): vector, matrix, or tensor representation of the ket state or dm state in the fock basis to prepare
            modes (list[int] or non-negative int): The mode(s) into which state is to be prepared. Needs not be ordered.
        """
        if isinstance(modes, int):
            modes = [modes]

        reduced_state = ops.partial_trace(data, self.num_modes, modes)

        self.data = np.tensordot(reduced_state, data, axes=0)

        if modes != list(range(self.num_modes - len(modes), self.num_modes)):
            mode_permutation = [
                x for x in range(self.num_modes) if x not in modes
            ] + modes
            scale = 2
            index_permutation = [
                scale * x + i for x in mode_permutation for i in (0, 1)
            ]  # two indices per mode if we have pure states
            index_permutation = np.argsort(index_permutation)

            self.data = np.transpose(self.data, index_permutation)

        self.state = FockState(
            state_data=self.data,
            num_modes=self.num_modes,
            cutoff_dim=self.cutoff,
            hbar=self.hbar,
        )

    def alloc(self, n=1):
        """allocate a number of modes at the end of the state."""
        # base_shape = [self._trunc for i in range(n)]

        vac = ops.vacuumStateMixed(n, self.cutoff)

        self.data = ops.tensor(self.state.dm(), vac, self.num_modes)
        self.state = FockState(
            state_data=self.data,
            num_modes=self.num_modes,
            cutoff_dim=self.cutoff,
            hbar=self.hbar,
        )

    def state_init(self, photon_number, modes):
        self.state_preparations.append((photon_number, modes))

    def _state_init(self, state_preparation: int, modes):
        vector = ops.fock_state(state_preparation, self.cutoff)
        self.data = np.outer(vector, vector.conjugate())
        self.state = FockState(
            state_data=self.data,
            num_modes=self.num_modes,
            cutoff_dim=self.cutoff,
            hbar=self.hbar,
        )
#        self.prepare_multimode(np.outer(vector, vector.conjugate()), modes)

        self.alloc()

    def execute(self):
        if len(self.state_preparations) > 0:
            for photon_number, modes in self.state_preparations:
                self._state_init(photon_number, modes)
        else:
            
            self.prepare_experiment()

        if len(self.channels) > 0:
            for channel, modes in self.channels:
                self.data = ops.apply_channel(
                    self.state, kraus_ops=channel, modes=modes
                )
                self.state = FockState(
                    state_data=self.data,
                    num_modes=self.num_modes,
                    cutoff_dim=self.cutoff,
                )
        if len(self.operations) > 0:

            for operator, modes in self.operations:
                self.data = ops.apply_gate_BLAS(
                    operator, self.state.dm(), modes, self.num_modes, self.cutoff
                )
                self.state = FockState(
                    state_data=self.data,
                    num_modes=self.num_modes,
                    cutoff_dim=self.cutoff,
                )
