"""
project_management module implements various
functionlaities regarding the project management
Such as:
 - saving project
 - creating project
 - loading project
"""

import json
from quasi.gui.board.board import Board
from quasi.gui.simulation.simulation_wrapper import SimulationWrapper
from quasi.gui.board.ports import BoardConnector

class Project():
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(Project, cls).__new__(cls)
            # Initialize your instance variables here if needed
        return cls.__instance

    def __init__(self):
        self.meta = {
            "location": None,
            "name": None,
        }

    def change_location(self, location):
        print("Location Changed")
        self.meta["location"]=location

    def change_project_name(self, name):
        self.meta["name"]=name

    def save(self):
        """
        This collectes all of the data
        and stores it into a json type of file
        """
        from quasi.gui.board.board import Board

        print(f"Saving {self.meta['location']}/{self.meta['name']}")

        # Get elements from the board
        board = Board.get_board()

        json_description={
            "meta":self.meta,
            "devices":[],
            "connections":[],
        }

        for d in board.content.controls:
            dt = f"{type(d.device_instance).__module__}.{type(d.device_instance).__name__}"
            device = {
                #"device": type(d.device_instance),
                "device": dt,
                "location": (d.left*2, d.top*2),
                "name": d.device_instance.ref.name,
                "uuid": d.device_instance.ref.uuid,
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
            print(signal)

        pl = f'{self.meta["location"]}/{self.meta["name"]}.json'
        with open(pl, 'w') as json_file:
            json.dump(json_description, json_file, indent=4)


    def load(self, project_path):
        with open(f"{project_path}") as f:
            data = json.load(f)
        board = Board.get_board()
        board.clear_board()
        bc = BoardConnector()

        self.meta = data["meta"]
        
        for d in data["devices"]:
            board.load_device(d["device"], d["location"], d["uuid"])

        for s in data["connections"]:
            bc.load_connection(s)
