from abc import ABCMeta, abstractmethod

class IServerSideProxy(metaclass=ABCMeta):
    """Interface class for a weather server broker proxy"""
    @abstractmethod
    def acknowledge_persistence(self, finished_ID):
        pass


class IDatabaseService(metaclass=ABCMeta):
    """Interface class for weather database services"""

    @abstractmethod
    def add_data(self, message):
        pass

    @abstractmethod
    def register_observer(self, observer):
        pass

    @abstractmethod
    def unregister_observer(self, observer):
        pass


class IDatabaseServiceFactory(metaclass=ABCMeta):
    """Abstract factory for weather database services"""

    @abstractmethod
    def create(self, db_file_name):
        pass