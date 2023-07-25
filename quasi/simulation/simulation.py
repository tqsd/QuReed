"""
Simulation Module
"""
# pylint: skip-file
import uuid
from dataclasses import dataclass

@dataclass
class DeviceInformation:
    """
    Device representation, used for registering the device with
    the Simulation singleton class
    """
    uuid : str
    name : str
    obj_ref : object


    def __init__(self, name:str, obj_ref:object):
        self.name = name
        self.obj_ref = obj_ref 
        self.uuid = str(uuid.uuid4())

    @property
    def device_type(self):
        return self.obj_ref.__class__.__name__

class Simulation:
    """Singleton object"""
    __instance = None

    """
    Simulation parameters
      + can be changed using setters and getters
    """
    dimensions = 30

    @staticmethod
    def get_instance():
        """
        Method that returns a single Simulation object
        """
        if Simulation.__instance is None:
            Simulation()
        return Simulation.__instance


    def __init__(self):
        """
        Initialization method
        """
        if Simulation.__instance is None:
            Simulation.__instance = self
            self.devices = []
        else:
            raise Exception("Simulation is a singleton class")

    def register_device(self, device_information:DeviceInformation):
        """
        Component registration in the simulation singleton object
        Should be called by initiation method of any device class.
        """
        self.devices.append(device_information)


    @classmethod
    def set_dimensions(cls, dimensions):
        cls.dimensions = dimensions

    @classmethod
    def get_dimensiosn(cls, dimensions):
        return cls.dimensions


    def list_devices(self):
        """
        Prints a table of devices registered with the simulation object
        """
        n = 10
        d = 10
        t = 25
        u = 36
        total_top =0
        total_bot = 11 + n + t + u - 4
        print("╭─"+ "DEVICES".center(total_bot, "─") +"─╮")
        print(f"│- {'NAME'.center(n, ' ')} - {'TYPE'.center(t, ' ')} - {'UUID'.center(u, ' ')} │")
        print("├─"+"─"*total_bot+"─┤")
        for d in self.devices:
            print(f"├─ {str(d.name).ljust(n)} : {str(d.device_type).ljust(t)} : {str(d.uuid).ljust(u)} │")
        print("╰─"+"─"*total_bot+"─╯")
