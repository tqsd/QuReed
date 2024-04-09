"""
Simulation Module
"""
# pylint: skip-file
from enum import Enum, auto
import uuid
from threading import Thread
import heapq
import mpmath

from dataclasses import dataclass
from quasi.signals.generic_bool_signal import GenericBoolSignal
from quasi.extra import Loggers, get_custom_logger

@dataclass
class DeviceInformation:
    """
    Device representation, used for registering the device with
    the Simulation singleton class
    """
    uuid : str
    name : str
    obj_ref : object


    def __init__(self, name:str, obj_ref:object, uid=None):
        self.name = name
        self.obj_ref = obj_ref 
        if uid is not None:
            self.uuid = uid
        else:
            self.uuid = str(uuid.uuid4())

    @property
    def device_type(self):
        return self.obj_ref.__class__.__name__


class SimulationType:
    FOCK = auto()
    MIXED = auto()

class SimulationEvent:
    """
    Simulation Event

    actions are scheduled using simulation events
    """
    def __init__(self, event_time, device, action, *args, **kwargs):
        self.event_time = event_time
        self.device = device
        self.action = action
        self.args = args
        self.kwargs = kwargs

    def __lt__(self, other):
        return self.event_time < other.event_time

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
            self.event_queue = []
            mpmath.mp.prec = 256
            self.current_time = mpmath.mpf('0')
            self.end_time = mpmath.mpf('0')
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

    def run_des(self, simulation_time):
        logger = get_custom_logger(Loggers.Simulation)
        logger.info("Starting Simulation")
        self.end_time += simulation_time
        while self.event_queue and self.current_time <= self.end_time:
            event = heapq.heappop(self.event_queue)
            logger.info("Processing Event for %s of type %s at %s" % (
                event.device.name,
                event.device.__class__.__name__,
                event.event_time))
            event.action(self.current_time)
            self.current_time = event.event_time

    def schedule_event(self, time, func, *args, **kwargs):
        event = SimulationEvent(time, func.__self__, func, *args, **kwargs)
        heapq.heappush(self.event_queue, event)

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

    def clear_all(self):
        for d in self.devices:
            del d
        self.devices = []
