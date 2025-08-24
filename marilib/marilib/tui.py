from abc import ABC, abstractmethod

class MarilibTUI(ABC):
    @abstractmethod
    def render(self, mari: "Marilib"):
        pass

    @abstractmethod
    def close(self):
        pass
