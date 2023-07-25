"""
Simulation Module
"""
# pylint: skip-file


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
        else:
            raise Exception("Simulation is a singleton class")

    def register_device(self):
        """
        Component registration in the simulation singleton object
        Should be called by initiation method of any device class.
        """
        pass


    @classmethod
    def set_dimensions(cls, dimensions):
        cls.dimensions = dimensions

    @classmethod
    def get_dimensiosn(cls, dimensions):
        return cls.dimensions
