from abc import ABC
from abc import abstractmethod


class BaseTool(ABC):

    @abstractmethod
    def run(self, **kwargs):
        pass