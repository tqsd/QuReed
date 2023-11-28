import os, errno
import platform
import json

class LocalData():

    """ LocalData is a singleton class """
    __instance = None

    @staticmethod
    def get_instance():
        if LocalData.__instance == None:
            LocalData()
        return LocalData.__instance


    def __init__(self): 
        if LocalData.__instance is None:
            self.data = None
            self.load_user_config()
        else:
            raise Exception("This is a singleton class")

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
            with open(filename, 'w') as config_file:
                json.dump({}, config_file)


    def load_user_config(self):
        try:
            with open(LocalData.get_config_file_path(), 'r') as file:
                data = json.load(file)
            self.data = data
        except FileNotFoundError:
            print(f"Error: File data.json file not found")
        except json.JSONDecodeError as e:
            print(f"Error Decoding JSON: {e}")
    

    def save_user_config(self):
        with open(LocalData.get_config_file_path(), "w") as cf:
            cf.write(json.dumps(self.data))


    def add_to_recent_projects(self, project, path):
        p = {"name":project, "paht":path}
        if "recent_projects" not in self.data.keys():
            self.data["recent_projects"] = []

        self.data["recent_projects"].insert(0, p)
        self.data["recent_projects"] = self.data["recent_projects"][:20]
        self.save_user_config()
        

            
