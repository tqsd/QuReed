"""
Simulation Module
"""

# pylint: skip-file
from typing import Type, TYPE_CHECKING
from enum import Enum, auto
import uuid
from threading import Thread
import heapq
import mpmath
from quasi.extra import Loggers, get_custom_logger
from dataclasses import dataclass
from quasi.signals.generic_bool_signal import GenericBoolSignal
from quasi.signals.generic_quantum_signal import GenericQuantumSignal
from quasi.experiment.experiment_manager import Experiment
from quasi.backend.backend import FockBackend, Backend
from quasi.backend.fock_first_backend import FockBackendFirst

if TYPE_CHECKING:
    from quasi.devices import GenericDevice


@dataclass
class DeviceInformation:
    """
    Device representation, used for registering the device with
    the Simulation singleton class
    """

    uuid: str
    name: str
    obj_ref: object

    def __init__(self, name: str, obj_ref: Type["GenericDevice"], uid=None):
        self.name = name
        self.obj_ref = obj_ref
        if uid is not None:
            self.uuid = uid
        else:
            self.uuid = str(uuid.uuid4())

    @property
    def device_type(self):
        return self.obj_ref.__class__.__name__

    @property
    def new_modes(self) -> int:
        """
        Computes number of new modes, the simulation
        would require
        """
        modes = 0
        quantum_outputs = [
            port
            for port in self.obj_ref.ports.values()
            if (port.direction == "output" and port.signal_type is GenericQuantumSignal)
        ]
        quantum_inputs = [
            port
            for port in self.obj_ref.ports.values()
            if (port.direction == "input" and port.signal_type is GenericQuantumSignal)
        ]
        # We create the modes for the outputs,
        # that can't be mapped to inputs
        if len(quantum_outputs) > len(quantum_inputs):
            modes += len(quantum_outputs) - len(quantum_inputs)

        # We create the modes for the empty inputs
        modes += len([port for port in quantum_inputs if port.signal is None])
        return modes


class SimulationType(Enum):
    FOCK = auto()
    GAUSSIAN = auto()


class SimulationEvent:
    """
    Simulation Event

    actions are scheduled using simulation events
    """

    def __init__(self, event_time, device, *args, **kwargs):
        if kwargs.get("signals") is None:
            kwargs["signals"] = {}
        self.event_time = event_time
        self.device = device
        self.args = args
        self.kwargs = kwargs

    def __lt__(self, other):
        return self.event_time < other.event_time

    def merge_event(self, new_event):
        if "signals" in new_event.kwargs:
            if "signals" in self.kwargs:
                # Merge the signals dictionaries
                for port, signal in new_event.kwargs["signals"].items():
                    self.kwargs["signals"][port] = signal
            else:
                # No signals in existing event, just add all from new_event
                self.kwargs["signals"] = new_event.kwargs["signals"]
        # Optionally merge args if needed
        self.args += new_event.args


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
            self.backend = FockBackendFirst
            self.devices = []
            self.initial_trigger_devices = []
            self.simulation_type = SimulationType.FOCK
            self.event_queue = []
            self.event_map = {}
            mpmath.mp.prec = 256
            self.current_time = mpmath.mpf("0")
            self.end_time = mpmath.mpf("0")
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
            time_as_float = float(event.event_time)
            logger.info(
                f"[{time_as_float:.3e}s] Processing Event for {event.device.name} of type {event.device.__class__.__name__}"
            )
            event.device.des(event.event_time, *event.args, **event.kwargs)
            # remove from the event map
            self.current_time = event.event_time
            key = (self.current_time, event.device)
            if key in self.event_map:
                del self.event_map[key]

    def schedule_event(self, time, device, *args, **kwargs):
        event = SimulationEvent(time, device, *args, **kwargs)
        key = (time, device)
        if key in self.event_map:
            existing_event = self.event_map[key]
            existing_event.merge_event(event)
        else:
            heapq.heappush(self.event_queue, event)
            self.event_map[key] = event

    def run(self):
        """
        Executes the experiment
        """
        # Determine number of modes
        modes = sum([d.new_modes for d in self.devices])
        if isinstance(self.backend, FockBackend):
            self.backend.set_number_of_modes(modes)
            self.backend.set_dimensions(self.dimensions)
            self.backend.initialize()

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

        if self.simulation_type == SimulationType.FOCK:
            exp = Experiment.get_instance()
            exp.execute()

    def register_triggers(self, *devices):
        """
        Given devices will be triggered in when
        simulation starts using classical signals
        """
        for d in devices:
            sig = GenericBoolSignal()
            d.register_signal(signal=sig, port_label="TRIGGER")
            d = [x for x in self.devices if x.obj_ref == d][0]
            if d not in self.initial_trigger_devices:
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
        title = " " + title + " "
        print("╭─" + title.center(total_bot, "─") + "─╮")
        print(
            f"│- {'NAME'.center(n, ' ')} - {'TYPE'.center(t, ' ')} - {'UUID'.center(u, ' ')} │"
        )
        print("├─" + "─" * total_bot + "─┤")
        for d in devices:
            print(
                f"├─ {str(d.name).ljust(n)} : {str(d.device_type).ljust(t)} : {str(d.uuid).ljust(u)} │"
            )
        print("╰─" + "─" * total_bot + "─╯")

    def clear_all(self):
        for d in self.devices:
            del d
        self.devices = []

    def set_backend(self, backend: Backend):
        self.backend = backend

    def get_backend(self) -> Backend:
        return self.backend
