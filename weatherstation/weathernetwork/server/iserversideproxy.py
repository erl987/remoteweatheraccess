from abc import ABCMeta, abstractmethod

class IServerSideProxy(metaclass=ABCMeta):
    """Interface class for a weather server broker proxy"""
    @abstractmethod
    def acknowledge_persistence(self, finished_ID):
        pass

    @abstractmethod
    def join(self):
        pass
