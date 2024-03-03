"""
This is the connection between the GUI and
the simulation engine
"""
from quasi.simulation import Simulation, DeviceInformation
from quasi.backend.fock_first_backend import FockBackendFirst
from quasi.experiment import Experiment


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
        self.simulation.list_devices()
        # We hardcode the backend for now
        self.simulation.set_backend(FockBackendFirst())
        self.simulation.run()
        # We print the experiment outcome
        exp = Experiment.get_instance()
        state = exp.state
        print(state.all_fock_probs())

    def add_device(self, device):
        self.devices.append(device)

    def get_device(self, uid):
        print(uid)
        d = [x for x in self.devices if x.ref.uuid == uid]
        for x in self.devices:
            print(x.ref)
        if len(d) == 1:
            return d[0]
        return None

    def create_connection(self, sig,
                          dev1, port_label_1,
                          dev2, port_label_2):
        dev1.register_signal(signal=sig, port_label=port_label_1)
        dev2.register_signal(signal=sig, port_label=port_label_2)
        self.signals.append(sig)


    def clear(self):
        self.simulation.clear_all()
        self.devices = []
        self.signals = []
