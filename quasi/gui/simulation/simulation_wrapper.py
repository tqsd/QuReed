"""
This is the connection between the GUI and
the simulation engine
"""
from quasi.simulation import Simulation, DeviceInformation
from quasi.backend.fock_first_backend import FockBackendFirst
from quasi.experiment import Experiment
from quasi.extra import Loggers, get_custom_logger
from quasi.gui.report import GuiLogHandler 

import subprocess

class SimulationWrapper:
    """
    SimulationWrapper is a Singleton which
    handles the flow of simulation and exposes        # We hardcode the backend for now

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
            self.simulation_time = 1
        self.simulation = Simulation.get_instance()

    def execute(self):
        """
        Execution Trigger
        """
        from quasi.gui.project import ProjectManager
        pm = ProjectManager()

        print(dir(pm))
        print(pm.venv)
        if pm.venv is None:
            print("Invalid project venv not configured")
            return

        python_executable = f"{pm.venv}/bin/activate"

        command = ["pip", "freeze"]

        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, errors = process.communicate()

        if process.returncode != 0:
            print("Error running simulation:")
            print(errors.decode())
        else:
            print("Simulation output:")
            print(output.decode())


    def add_device(self, device):
        self.devices.append(device)

    def remove_device(self, device):
        self.devices.remove(device)

    def get_device(self, uid):
        d = [x for x in self.devices if x.ref.uuid == uid]
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
