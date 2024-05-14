from pathlib import Path
import toml
import subprocess


class ProjectManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProjectManager, cls).__new__(cls)
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
