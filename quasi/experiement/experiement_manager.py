class Experiement:
    """Singleton object"""

    __instance = None

    @staticmethod
    def get_instance():
        """
        Method that returns a single Experiment object
        """
        if Experiement.__instance is None:
            Experiement()
        return Experiement.__instance

    def __init__(self):
        """
        Initialization method
        """
        if Experiement.__instance is None:
            Experiement.__instance = self
        else:
            raise Exception("Experiment is a singleton class")
        
    def state_init():
        pass
    
    def add_operation():
        pass