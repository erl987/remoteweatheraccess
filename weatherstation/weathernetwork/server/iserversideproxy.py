from abc import ABCMeta, abstractmethod

class IServerSideProxy(metaclass=ABCMeta):
    """Interface class for a weather server broker proxy"""
    @abstractmethod
    def register_listener(self, observer):
        pass

    @abstractmethod
    def remove_listener(self, observer):
        pass

    @abstractmethod
    def acknowledge_persistence(self, finished_ID):
        pass

    @abstractmethod
    def on_data_received(self, message_ID, station_ID):
        pass

    @abstractmethod
    def wait_for_next_data(self):
        pass
