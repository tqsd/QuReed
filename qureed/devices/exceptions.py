class NoPortException(Exception):
    """
    Raised when port, which should be accessed doesn't exist
    """


class PortConnectedException(Exception):
    """
    Raised when Signal is already registered for the port.
    """


class PortDirectionException(Exception):
    """
    Raised when connecting ports with the same direction
    """


class NoReferenceException(Exception):
    """
    Raised when accessing non existent reference
    """

class PortMissingAttributesException(Exception):
    """
    Raised when Attributes are not specified
    """

class PortSignalMismatchException(Exception):
    """
    Raised when signal doesn't match the port description
    """
