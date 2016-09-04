from weathernetwork.server.iserversideproxy import IServerSideProxy
from weathernetwork.server.weathermessage import WeatherMessage

class MockServerSideProxy(IServerSideProxy):
    """Interface class for a weather server broker proxy testing mock"""

    def __init__(self):
        self._observers = [];


    def register_listener(self, observer):
        """ Registers a new listener.
        :param observer:    new listener to be registered
        :type observer:     IWeatherPersistenceService
        """
        self._observers.append(observer)


    def remove_listener(self, observer):
        self._observers.remove(observer)


    def acknowledge_persistence(self, finished_ID):
        print(finished_ID)


    def on_data_received(self, message_ID, station_ID, data):
        message = WeatherMessage(message_ID, station_ID, data)
        self._notify_listeners(message)


    def _notify_listeners(self, message):
        for observer in self._observers:
            observer.add_data(message)