"""
This is the connection between the GUI and
the simulation engine
"""
import logging
from quasi.simulation import Simulation, DeviceInformation
from quasi.backend.fock_first_backend import FockBackendFirst
from quasi.experiment import Experiment
from quasi.extra import Loggers, get_custom_logger
from quasi.gui.report import GuiLogHandler 
from .remote_log_handler import (
    find_free_port,
    start_tcp_server
)

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
        pm.save()

        if pm.venv is None:
            return

        python_executable = f"{pm.venv}/bin/quasi-execute"
        PORT = find_free_port()
        server, server_thread = start_tcp_server(PORT)
        command = [python_executable, "--scheme" , f"{pm.path}/experiment.json",
                   "--sim_type", "des", "--duration", "10", "--port", str(PORT)]
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()  # This waits for the subprocess to complete
            print("STDOUT:", stdout.decode())
            print("STDERR:", stderr.decode())
        except Exception as e:
            print("An error occured:", str(e))
        finally:
            server.shutdown_server()
            server_thread.join()
            logging.info("TCP server has been shut down")


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
