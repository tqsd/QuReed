from pathlib import Path
import toml
import subprocess
import importlib
import os
import json
import pathlib
import platform
import sys
import inspect

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
            cls._instance.packages = []
            cls._instance.current_scheme = None
        return cls._instance

    def configure(self, **kwargs):
        if "path" in kwargs:
            self.path = Path(kwargs["path"])
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
            config_path = Path(self.path) / "config.toml"
            if config_path.exists():
                config = toml.load(config_path)
                packages = config.get("packages", [])

        # Ensure virtual environment path is set
        if not hasattr(self, "venv"):
            return

        if platform.system() == "Windows":
            python_exec = Path(self.venv) / "Scripts" / "python.exe"
        else:
            python_exec = Path(self.venv) / "bin" / "python"

        command = [str(python_exec), "-m", "pip", "install"] + list(packages)
        try:
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error: Failed to install packages. {e}")
            return

        # Update config.toml file
        config_path = Path(self.path) / "config.toml"
        config = toml.load(config_path) if config_path.exists() else {}
        config["packages"] = list(packages)
        with open(config_path, "w") as file:
            toml.dump(config, file)

    def load_class_from_file(self, relative_module_path):
        # Construct the full path to the module file
        full_path = Path(self.path) / relative_module_path
        
        # Resolve the path to ensure it's absolute and normalize any irregular path components
        full_path = full_path.resolve()
        if not full_path.exists():
            raise FileNotFoundError(f"No such file: {full_path}")

        # Debug prints for verification
        if not full_path.is_relative_to(self.path):
            raise ValueError("Attempted to access a file outside of the base directory")

        # Convert the full path to a dot-separated module path relative to the base path
        module_str = str(full_path.relative_to(self.path)).replace('/', '.').replace('\\', '.')

        # Only strip the '.py' suffix if it is at the end
        if module_str.endswith('.py'):
            module_str = module_str[:-3]

        
        class_name = str(Path(full_path).name)[:-3]
        class_name = ''.join(x.capitalize() or '_' for x in class_name.split('_'))
        # Dynamically import the module
        module = importlib.import_module(module_str)
        
        # Inspect the module and return the first found class
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if name == class_name and obj.__module__ == module.__name__:
                return obj

    def get_file_tree(self):
        """
        Gets the file tree of the project
        """
        def list_files(directory):
            tree = []
            for entry in os.listdir(directory):
                full_path = os.path.join(directory, entry)
                if entry in ["None", "__init__.py", "__pycache__", ".git", ".gitignore"]:
                    continue
                if "~" in entry or entry.startswith("."):
                    continue
                if os.path.isdir(full_path):
                    if entry == ".venv":
                        continue
                    relative_path = os.path.relpath(full_path, self.path)
                    tree.append({relative_path:list_files(full_path)})
                else:
                    relative_path = os.path.relpath(full_path, self.path)
                    tree.append(relative_path)
            return tree
        if self.path is None:
            return []
        lst = list_files(self.path)
        def sort_files_folders(items):
            def sort_key(item):
                if isinstance(item, str):
                    return (0, item)  # File
                elif isinstance(item, dict):
                    return (1, next(iter(item)))  # Folder
                return (2, None)  # Fallback case, should not occur

            # Sort items at the current level
            items.sort(key=sort_key)

            # Recursively sort directories
            for item in items:
                if isinstance(item, dict):
                    for key in item:
                        sort_files_folders(item[key])
        sort_files_folders(lst)
        return lst

    def open_project(self, project_path):
        from quasi.gui.panels.project_panel import ProjectPanel

        self.path = project_path
        path = Path(self.path)
        self.name = path.name
        self.venv = path / ".venv"

        devices_path = os.path.join(self.path, 'custom', 'devices')
        if str(self.path) not in sys.path:
            sys.path.append(str(self.path))

        if not self.venv.exists():
            self.create_venv()
            self.install()

        pm = ProjectPanel.get_instance()
        pm.update_project(self.path)
        
    def open_scheme(self, scheme):
        board = Board.get_board()
        # save existing scheme to memory
        if self.current_scheme is not None:
            self.modified_schemes[self.current_scheme] = self._capture_board_dict()

        self.current_scheme = scheme
        data = self._get_scheme_dict(scheme)
        board.clear_board()
        board.set_new_scheme(scheme)
        bc = BoardConnector()
        if data.get("devices") is not None:
            for d in data["devices"]:
                board.load_device(d["device"], d["location"], d["uuid"], d.get("values"), d["name"])

            for s in data["connections"]:
                bc.load_connection(s)

        self.current_scheme = scheme

    def save(self):
        """
        Saves all schemes
        """
        self.modified_schemes[self.current_scheme] = self._capture_board_dict()

        for scheme, data in self.modified_schemes.items():
            with open(f"{self.path}/{scheme}", "w") as json_file:
                json.dump(
                    data, json_file, indent=4
                )

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
                    "name": d.device_instance.name,
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

    def create_venv(self, path=None):
        if path is None:
            path = self.path
        python_command = "python3" if platform.system() != "Windows" else "python"
        subprocess.run([python_command, "-m", "venv",  os.path.join(path, ".venv")], check=True)
