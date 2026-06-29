from abc import ABC, abstractmethod


class Base_Manager(ABC):

    @abstractmethod
    def init(self):
        pass