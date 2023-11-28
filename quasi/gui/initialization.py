import os, errno
import platform
import json

class LocalData():

    @classmethod
    def initialize(cls):
        LocalData.create_config_dir_if_not_exist()
        LocalData.create_config_file()

    @classmethod
    def get_config_dir(cls):
        """
        Gets the config dir
        """
        pf = platform.system()
        if pf == "Linux":
            return os.path.expanduser("~/.config/quasi/")
            pass
        elif pf== "Darwin":
            return ""
        elif pf== "Windows":
            return ""
        
    @classmethod
    def create_config_dir_if_not_exist(cls):
        directory = LocalData.get_config_dir()
        print(f"Creating dir {directory}")
        try:
            os.makedirs(directory)
        except OSError as e:
            if e.errno != errno.EEXIST:
                print(e)

    @classmethod
    def get_config_file_path(cls):
        return  f"{LocalData.get_config_dir()}/data.json"

    @classmethod
    def create_config_file(cls):
        filename = LocalData.get_config_file_path()
        if not os.path.exists(filename):
            open(filename, 'w').close()


    @classmethod
    def get_from_config_dict(cls):
        try:
            with open(LocalData.get_config_file_path(), 'r') as file:
                data = json.load("file")
            return data
        except FileNotFoundError:
            print(f"Error: File data.json file not found")
        except json.JSONDecodeError as e:
            print(f"Error Decoding JSON: {e}")
    

    @classmethod
    def write_to_config_file(cls, key, data):
        pass
