"""
This is the connection between the GUI and
the simulation engine
"""


class SimulationWrapper:
    """
    SimulationWrapper is a Singleton which
    handles the flow of simulation and exposes
    its control to the gui
    """
    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super(SimulationWrapper, cls).__new__(cls)
            cls.__instance.initialized = False
        return cls.__instance

    def __init__(self):
        # pylint: disable=access-member-before-definition
        if not self.initialized:
            self.initialized = True

    def execute(self):
        print("START THE SIMULATION")

    def add_device(self, device):
        print("ADDED A DEVICE")
        print(device)

    def create_connection(self):
        print("CREATING CONNECTION")
