"""
This is the connection between the GUI and
the simulation engine
"""
from quasi.simulation import Simulation, DeviceInformation


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
            self.devices = []
            self.signals = []
        self.simulation = Simulation.get_instance()

    def execute(self):
        """
        Execution Trigger
        """
        print("START THE SIMULATION")
        self.simulation.list_devices()
        print(self.signals)
        self.simulation.run()

    def add_device(self, device, coordinator):
        self.devices.append(device)

    def create_connection(self, sig,
                          dev1, port_label_1,
                          dev2, port_label_2):
        print("BACKEND CONNECTION")
        print(dev1)
        dev1.register_signal(signal=sig, port_label=port_label_1)
        dev2.register_signal(signal=sig, port_label=port_label_2)
        self.signals.append(sig)
        print("CREATING CONNECTION")
