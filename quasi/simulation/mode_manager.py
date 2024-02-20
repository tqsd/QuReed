"""
This file implements a mode
manager
"""
import uuid

from quasi.simulation import Simulation
from quasi._math.fock.ops import vacuum_state



class ModeManager():
    """
    Mode managing logic
    SINGLETON
    """
    __instance = None

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super(ModeManager, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self):
        if not self.__initialized:
            self.__initialized = True
            self.simulation = Simulation.get_instance()
            self.modes = {}

    def create_new_mode(self) -> str:
        """
        Creates a new mode in vacuum state and returns its id.
        """
        new_mode_id = uuid.uuid4()
        mode = vacuum_state(
            2,
            Simulation.dimensions
        )
        self.modes[new_mode_id] = mode
        return new_mode_id

    def clear_modes(self) -> None:
        self.modes = {}

    def get_mode(self, mode_id: str):
        return self.modes[mode_id]

    def remove_mode(self, mode_id: str) -> None:
        pass
