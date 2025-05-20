from abc import ABC
from dataclasses import dataclass


@dataclass()
class GenericError(ABC):
    """
    Base class to formally compute and communicate errors
    """

    description: str = ""
