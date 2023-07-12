"""
Simulation Module
"""
# pylint: skip-file


class Simulation:
    """Singleton object"""

    __instance = None

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
        else:
            raise Exception("Simulation is a singleton class")
