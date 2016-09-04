from abc import ABCMeta, abstractmethod

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