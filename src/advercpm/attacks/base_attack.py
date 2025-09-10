from abc import ABC, abstractmethod
from typing import Dict, Any


class Attack(ABC):
    """
    Abstract base class for adversarial CPM attacks.
    """

    def __init__(self, parameters: Dict[str, Any]):
        self.parameters = parameters

    @abstractmethod
    def apply(self, cpm_frame: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply the attack to a single CPM frame.

        Args:
            cpm_frame: Parsed CPM data (from YAML/JSON).

        Returns:
            Modified CPM frame.
        """
        pass

    def __repr__(self):
        return f"{self.__class__.__name__}(parameters={self.parameters})"
