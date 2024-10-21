import importlib
import inspect
import json
import os
import pathlib
import platform
import subprocess
import sys
from pathlib import Path

import toml

from qureed.gui.board.board import Board
from qureed.gui.board.device import Device
from qureed.gui.board.ports import BoardConnector
from qureed.gui.board.variable import VariableComponent
from qureed.gui.simulation.simulation_wrapper import SimulationWrapper


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
            cls._instance.base_path = None
            # Determine if running in a PyInstaller bundle
            if getattr(sys, "frozen", False):
                # If the application is run from a PyInstaller bundle
                cls._instance.base_path = Path(sys._MEIPASS)
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

    def load_config(self):
        """Load the existing configuration from a TOML file."""
        config_path = Path(self.path) / "config.toml"
        if config_path.exists():
            with open(config_path, "r") as file:
                return toml.load(file)
        return {}

    def update_config(self, updates):
        """
        Update the configuration file with new values.

        Args:
        updates (dict): A dictionary containing configuration updates.
        """

        config_path = Path(self.path) / "config.toml"
        with open(config_path, "r") as f:
            config = toml.load(f)

        # Update the configuration with new values
        for key, value in updates.items():
            if isinstance(value, list):
                # Ensure no duplicate entries in lists
                existing_items = set(config.get(key, []))
                updated_items = existing_items.union(set(value))
                config[key] = list(updated_items)
            else:
                # Update or add new key-value pairs
                config[key] = value

        print("-------------------------------------------")
        # Write the updated configuration back to the file
        with open(config_path, "w") as file:
            toml.dump(config, file)

    def install(self, *packages):
        packages = packages if packages else self.packages
        os_name = platform.system().lower()

        wheel_dir = None
        if not self.base_path is None:
            wheel_dir = Path(self.base_path) / "wheels" / os_name

        if not packages:
            config_path = Path(self.path) / "config.toml"
            if config_path.exists():
                config = toml.load(config_path)
                packages = config.get("packages", [])
        else:
            if packages:
                self.update_config({"packages": list(packages)})

        python_executable = (
            Path(self.venv) / "bin" / "python"
            if os_name != "windows"
            else Path(self.venv) / "Scripts" / "python.exe"
        )
        for package in packages:
            wheel_files = None
            if not wheel_dir is None:
                wheel_files = list(wheel_dir.glob(f"{package}*.whl"))
            print(f"Searching for wheels in {wheel_dir} for package {package}")
            if wheel_files:
                wheel_file = wheel_files[0]
                subprocess.run(
                    [str(python_executable), "-m", "pip", "install", str(wheel_file)],
                    check=True,
                )
            else:
                print(f"NO WHEEL FOR {package}")
                if package == "qureed":
                    subprocess.run(
                        [
                            str(python_executable),
                            "-m",
                            "pip",
                            "install",
                            "git+ssh://git@github.com/tqsd/qureed.git@master",
                        ],
                        check=True,
                    )
                if package == "photon_weave":
                    subprocess.run(
                        [
                            str(python_executable),
                            "-m",
                            "pip",
                            "install",
                            "git+ssh://git@github.com/tqsd/photon_weave.git@master",
                        ],
                        check=True,
                    )

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
        module_str = (
            str(full_path.relative_to(self.path)).replace("/", ".").replace("\\", ".")
        )

        # Only strip the '.py' suffix if it is at the end
        if module_str.endswith(".py"):
            module_str = module_str[:-3]

        class_name = str(Path(full_path).name)[:-3]
        class_name = "".join(x.capitalize() or "_" for x in class_name.split("_"))
        # Dynamically import the module
        print(module_str)
        from photon_weave.state.composite_envelope import CompositeEnvelope

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
                if entry in [
                    "None",
                    "__init__.py",
                    "__pycache__",
                    ".git",
                    ".gitignore",
                    ".venv"
                ]:
                    continue
                if "~" in entry or entry.startswith("."):
                    continue
                if os.path.isdir(full_path):
                    if entry == ".venv":
                        continue
                    relative_path = os.path.relpath(full_path, self.path)
                    tree.append({relative_path: list_files(full_path)})
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
        from qureed.gui.panels.project_panel import ProjectPanel

        self.path = project_path
        path = Path(self.path)
        self.name = path.name
        self.venv = path / ".venv"

        devices_path = os.path.join(self.path, "custom", "devices")
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
                board.load_device(
                    d["device"], d["location"], d["uuid"], d.get("values"), d["name"]
                )

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
                json.dump(data, json_file, indent=4)

    def _capture_board_dict(self):
        board = Board.get_board()

        json_description = {
            "devices": [],
            "connections": [],
        }

        for d in board.content.controls:
            if isinstance(d, Device):
                dt = f"{type(d.device_instance).__module__}.{type(d.device_instance).__name__}"
                device = {
                    # "device": type(d.device_instance),
                    "device": dt,
                    "location": (d.left * 2, d.top * 2),
                    "name": d.device_instance.name,
                    "uuid": d.device_instance.ref.uuid,
                }
                json_description["devices"].append(device)
            elif isinstance(d, VariableComponent):
                dt = f"{type(d.device_instance).__module__}.{type(d.device_instance).__name__}"
                device = {
                    # "device": type(d.device_instance),
                    "device": dt,
                    "location": (d.left * 2, d.top * 2),
                    "name": d.device_instance.ref.name,
                    "uuid": d.device_instance.ref.uuid,
                    "values": d.device_instance.values,
                }
                json_description["devices"].append(device)

        sim_wrapper = SimulationWrapper()
        for s in sim_wrapper.signals:
            signal = {"signal": f"{type(s).__module__}.{type(s).__name__}", "conn": []}
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
        subprocess.run(
            [python_command, "-m", "venv", os.path.join(path, ".venv")], check=True
        )
