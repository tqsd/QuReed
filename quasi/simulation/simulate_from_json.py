"""
This module handles execution from json schemes
"""
import argparse
import json
import logging
from logging.handlers import SocketHandler
import sys
from pathlib import Path
import socket
import struct
import pickle

from quasi.gui.simulation import SimulationWrapper
from quasi.gui.board.board import get_class_from_string
from quasi.gui.board.ports import BoardConnector
from quasi.extra import Loggers, get_custom_logger

class LengthPrefixedSocketHandler(logging.handlers.SocketHandler):
    def makePickle(self, record):
        # Create a pickle of the log record
        record_dict = record.__dict__
        data = pickle.dumps(record_dict)
        # Prefix the data with its length (using network byte order)
        return struct.pack('>L', len(data)) + data

class JsonExecution():
    def __init__(self, **kwargs):
        self.main_scheme = str(kwargs.get("scheme"))
        self.simulation_type = kwargs.get("sim_type")
        self.duration = kwargs.get("duration")
        self.port = kwargs.get("port")
        self.sw = SimulationWrapper()
        self.schemes = {}

        base_path = Path(self.main_scheme).parent
        if str(base_path) not in sys.path:
            sys.path.append(str(base_path))

    def assemble_simulation(self):
        self._get_scheme_dict(self.main_scheme)
        if self.schemes[self.main_scheme].get("devices") is not None:
            for d in self.schemes[self.main_scheme]["devices"]:
                dev_class = get_class_from_string(d["device"])
                dev_instance = dev_class(uid=d["uuid"])
                if "values" in d:
                    dev_instance.values = d["values"]
                self.sw.add_device(dev_instance)
            for connection in self.schemes[self.main_scheme]["connections"]:
                signal_class = get_class_from_string(connection["signal"])
                dev1 = self.sw.get_device(connection["conn"][0]["device_uuid"])
                pl1 = connection["conn"][0]["port"]
                dev2 = self.sw.get_device(connection["conn"][1]["device_uuid"])
                pl2 = connection["conn"][1]["port"]
                self.sw.create_connection(
                    sig=signal_class(),
                    dev1=dev1,
                    port_label_1=pl1,
                    dev2=dev2,
                    port_label_2=pl2
                )

    def configure_loggers(self):
        loggerA = get_custom_logger(Loggers.Devices)
        loggerB = get_custom_logger(Loggers.Simulation)
        loggerC = get_custom_logger(Loggers.Simulation)
        if self.port is not None:
            socket_handler = LengthPrefixedSocketHandler('localhost', self.port)
            loggerA.addHandler(socket_handler)
            loggerB.addHandler(socket_handler)
            loggerC.addHandler(socket_handler)
        
    def run(self):
        simulation_logger = get_custom_logger(Loggers.Simulation)
        
        match self.simulation_type:
            case "des":
                try:
                    self.sw.simulation.run_des(self.duration)
                except Exception as e:
                    simulation_logger.error(f"An error occurred during DES simulation: {e}")


    def _get_scheme_dict(self, scheme):
        with open(scheme, 'r', encoding='UTF-8') as f:
            self.schemes[scheme] = json.load(f)
        





def main():
    parser = argparse.ArgumentParser(description="Execute quasi simulation using JSON description.")
    parser.add_argument("--scheme", type=str, required=True, help="Path to the main json scheme to execute")
    parser.add_argument("--sim_type", type=str, default="des", help="Type of simulation")
    parser.add_argument('--duration', type=int, help='Duration of the simulation, required only for DES type.')

    parser.add_argument('--port', type=int, help='Log connection port', required=False)
    
    args  = parser.parse_args()

    if args.sim_type == "des" and args.duration is None:
        parser.error("The --duration argument is required when --sim_type is 'des'")



    JE = JsonExecution(**vars(args))
    JE.assemble_simulation()
    print("Running Simulation")
    JE.configure_loggers()
    JE.run()
    print("Completed")



if __name__ == "__main__":
    print("Executing from json")
