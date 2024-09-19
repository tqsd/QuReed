"""
This is the connection between the GUI and
the simulation engine
"""

import logging
import platform
import subprocess
import threading

from qureed.extra import Loggers, get_custom_logger
from qureed.gui.report import GuiLogHandler
from qureed.simulation import Simulation

from .remote_log_handler import find_free_port, start_tcp_server


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
            self._setup_logging()
        self.simulation = Simulation.get_instance()

    def execute(self):
        """
        Execution Trigger
        """
        from qureed.gui.project import ProjectManager
        from qureed.gui.report import Report

        pm = ProjectManager()
        pm.save()

        if pm.venv is None:
            return

        if Report._instance is not None:
            r = Report._instance
            r.clean_logs()

        system = platform.system()
        if system == "Windows":
            python_executable = f"{pm.venv}\\Scripts\\qureed-execute"
        else:  # Assume UNIX-like for any other system
            python_executable = f"{pm.venv}/bin/qureed-execute"
        PORT = find_free_port()
        server, server_thread = start_tcp_server(PORT)
        command = [
            python_executable,
            "--scheme",
            f"{pm.path}/experiment.json",
            "--sim_type",
            "des",
            "--duration",
            "10",
            "--port",
            str(PORT),
        ]
        try:
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

            # Thread to read stdout
            def read_stdout():
                for line in iter(process.stdout.readline, b""):
                    self.logger.info(line.decode().strip())

            # Thread to read stderr
            def read_stderr():
                for line in iter(process.stderr.readline, b""):
                    self.logger.error(line.decode().strip())

            stdout_thread = threading.Thread(target=read_stdout)
            stderr_thread = threading.Thread(target=read_stderr)

            stdout_thread.start()
            stderr_thread.start()

            stdout_thread.join()
            stderr_thread.join()

            process.stdout.close()
            process.stderr.close()

        except Exception as e:
            print(e)
            self.logger.error(f"An error occurred: {str(e)}")
        finally:
            server.shutdown_server()  # This calls the updated shutdown_server method
            server_thread.join()  # Wait for the server thread to finish
            self.logger.info("TCP server has been shut down")

    def _setup_logging(self):
        self.logger = logging.getLogger("SimulationWrapper")
        self.logger.setLevel(logging.DEBUG)
        self.log_handler = GuiLogHandler()
        for log_name in Loggers:
            custom_logger = get_custom_logger(log_name)
            custom_logger.addHandler(self.log_handler)

    def add_device(self, device):
        self.devices.append(device)

    def remove_device(self, device):
        self.devices.remove(device)

    def get_device(self, uid):
        d = [x for x in self.devices if x.ref.uuid == uid]
        if len(d) == 1:
            return d[0]
        return None

    def create_connection(self, sig, dev1, port_label_1, dev2, port_label_2):
        dev1.register_signal(signal=sig, port_label=port_label_1)
        dev2.register_signal(signal=sig, port_label=port_label_2)
        self.signals.append(sig)

    def remove_connection(self, sig):
        signal_to_remove = None
        self.signals.remove(sig)

    def clear(self):
        self.simulation.clear_all()
        self.devices = []
        self.signals = []
