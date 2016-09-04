from abc import ABCMeta, abstractmethod

class IWeatherPersistenceService(metaclass=ABCMeta):
    """Interface class for a service storing weather data in a database"""

    @abstractmethod
    def add_data(self, message):
        pass

    @abstractmethod
    def wait_for_next_data(self):
        pass