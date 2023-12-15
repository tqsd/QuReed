"""
Simulation Module
"""
# pylint: skip-file
from enum import Enum, auto
import uuid
from threading import Thread

from dataclasses import dataclass
from quasi.signals.generic_bool_signal import GenericBoolSignal

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


class SimulationType:
    FOCK = auto()
    MIXED = auto()


class Simulation:
    """Singleton object"""

    __instance = None

    """
    Simulation parameters
      + can be changed using setters and getters
    """
    dimensions = 10

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
            self.initial_trigger_devices = []
            self.simulation_type = SimulationType.FOCK
        else:
            raise Exception("Simulation is a singleton class")

    def register_device(self, device_information: DeviceInformation):
        """
        Component registration in the simulation singleton object
        Should be called by initiation method of any device class.
        """
        self.devices.append(device_information)

    def set_simulation_type(self, simulation_type: SimulationType):
        self.simulation_type = simulation_type


    @classmethod
    def set_dimensions(cls, dimensions):
        cls.dimensions = dimensions

    @classmethod
    def get_dimensions(cls):
        return cls.dimensions

    def run(self):
        for d in self.initial_trigger_devices:
            d = d.obj_ref
            sig = d.ports["TRIGGER"].signal
            sig.set_contents = True
            sig.set_computed()
        processes = []
        for d in self.devices:
            p = Thread(target=d.obj_ref.compute_outputs, args=(d.obj_ref,))
            processes.append(p)
        for p in processes:
            p.start()
        for p in processes:
            p.join()



    def register_triggers(self, *devices):
        """
        Given devices will be triggered in when
        simulation starts using classical signals
        """
        for d in devices:
            sig = GenericBoolSignal()
            d.register_signal(signal=sig, port_label="TRIGGER")
            d = [x for x in self.devices if x.obj_ref == d][0]
            if not d in self.initial_trigger_devices:
                self.initial_trigger_devices.append(d)


    def list_devices(self):
        self._list_devices(self.devices, "DEVICES")

    def list_triggered_devices(self):
        self._list_devices(self.initial_trigger_devices, "TRIGGERED DEVICES")

    def _list_devices(self, devices, title):
        """
        List a table of given device list with title
        """
        n = 10
        d = 10
        t = 25
        u = 36
        total_bot = 11 + n + t + u - 4
        title = " "+title+" "
        print("╭─" + title.center(total_bot, "─") + "─╮")
        print(f"│- {'NAME'.center(n, ' ')} - {'TYPE'.center(t, ' ')} - {'UUID'.center(u, ' ')} │")
        print("├─"+"─"*total_bot+"─┤")
        for d in devices:
            print(f"├─ {str(d.name).ljust(n)} : {str(d.device_type).ljust(t)} : {str(d.uuid).ljust(u)} │")
        print("╰─"+"─"*total_bot+"─╯")
