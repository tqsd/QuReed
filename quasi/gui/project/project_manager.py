from pathlib import Path
import toml
import subprocess
import os
import json
import pathlib

from quasi.gui.board.board import Board
from quasi.gui.board.ports import BoardConnector
from quasi.gui.board.device import Device
from quasi.gui.board.variable import VariableComponent
from quasi.gui.simulation.simulation_wrapper import SimulationWrapper



class ProjectManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProjectManager, cls).__new__(cls)
            cls._instance.path = None
            cls._instance.venv = None
            cls._instance.current_scheme = None
            cls._instance.modified_schemes = {}
        return cls._instance

    def configure(self, **kwargs):
        if "path" in kwargs:
            self.path = kwargs["path"]
            path = Path(self.path)
            self.name = path.name

            # Assume config.toml is in the base project directory
            config_path = path / "config.toml"
            if config_path.exists():
                config = toml.load(config_path)
                self.packages = config.get("packages", [])
            else:
                self.packages = []

        if "venv" in kwargs:
            self.venv = kwargs["venv"]

    def install(self, *packages):
        # Use packages from arguments or fallback to config.toml packages
        packages = packages if packages else self.packages
        if not packages:
            print("No packages to install.")
            return

        # Ensure virtual environment path is set
        if not hasattr(self, "venv"):
            print("Virtual environment path not set.")
            return

        # Construct the path to the Python executable in the virtual environment
        python_exec = Path(self.venv) / "bin" / "python"

        # Execute pip install for the packages
        command = [str(python_exec), "-m", "pip", "install"] + list(packages)
        subprocess.run(command, check=True)

        # Update config.toml file
        config_path = Path(self.path) / "config.toml"
        config = toml.load(config_path) if config_path.exists() else {}
        config["packages"] = list(packages)
        with open(config_path, "w") as file:
            toml.dump(config, file)

    def get_file_tree(self):
        """
        Gets the file tree of the project
        """
        def list_files(directory):
            tree = []
            for entry in os.listdir(directory):
                full_path = os.path.join(directory, entry)
                if os.path.isdir(full_path):
                    if entry == ".venv":
                        continue
                    tree.append({entry:list_files(full_path)})
                else:
                    tree.append(entry)
            return tree
        if self.path is None:
            return []
        return list_files(self.path)

    def open_project(self, project_path):
        from quasi.gui.panels.project_panel import ProjectPanel

        self.path = project_path
        path = Path(self.path)
        self.name = path.name

        pm = ProjectPanel.get_instance()
        pm.update_project(self.path)
        
    def open_scheme(self, scheme):
        board = Board.get_board()
        # save existing scheme to memory
        print(self.current_scheme)
        if self.current_scheme is not None:
            self.modified_schemes[self.current_scheme] = self._capture_board_dict()

        data = self._get_scheme_dict(scheme)
        board.clear_board()
        bc = BoardConnector()
        print(data)
        if data.get("devices") is not None:
            for d in data["devices"]:
                board.load_device(d["device"], d["location"], d["uuid"], d.get("values"))

            for s in data["connections"]:
                bc.load_connection(s)

        self.current_scheme = scheme
        
    def save_scheme(self):
        pass

    def save(self):
        """
        Saves all
        """

    def _capture_board_dict(self):
        board = Board.get_board()

        json_description={
            "devices":[],
            "connections":[],
        }

        for d in board.content.controls:
            if isinstance(d, Device):
                dt = f"{type(d.device_instance).__module__}.{type(d.device_instance).__name__}"
                device = {
                    #"device": type(d.device_instance),
                    "device": dt,
                    "location": (d.left*2, d.top*2),
                    "name": d.device_instance.ref.name,
                    "uuid": d.device_instance.ref.uuid,
                }
                json_description["devices"].append(device)
            elif isinstance(d, VariableComponent):
                dt = f"{type(d.device_instance).__module__}.{type(d.device_instance).__name__}"
                device = {
                    #"device": type(d.device_instance),
                    "device": dt,
                    "location": (d.left*2, d.top*2),
                    "name": d.device_instance.ref.name,
                    "uuid": d.device_instance.ref.uuid,
                    "values": d.device_instance.values
                }
                json_description["devices"].append(device)
        
        sim_wrapper = SimulationWrapper()
        for s in sim_wrapper.signals:
            signal = {
                "signal": f"{type(s).__module__}.{type(s).__name__}",
                "conn": []
            }
            for p in s.ports:
                d = {}
                d["device_uuid"] = p.device.ref.uuid
                d["port"] = p.label
                signal["conn"].append(d)

            json_description["connections"].append(signal)
        return json_description

    def _get_scheme_dict(self, scheme):
        if scheme in self.modified_schemes:
            return self.modified_schemes[scheme]
        with open(f"{self.path}/{scheme}") as f:
            data = json.load(f)
        return data
