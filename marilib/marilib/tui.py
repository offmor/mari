from abc import ABC, abstractmethod

from marilib.marilib import MarilibBase


class MarilibTUI(ABC):
    @abstractmethod
    def render(self, mari: MarilibBase):
        pass

    @abstractmethod
    def close(self):
        pass
