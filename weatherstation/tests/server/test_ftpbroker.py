#import unittest
#from weathernetwork.server.ftpbroker import FTPServerSideProxy
#from weathernetwork.server.sqldatabase import SQLDatabaseServiceFactory
#from weathernetwork.server.interface import IServerSideProxy
#from weathernetwork.server.weathermessage import WeatherMessage
#from multiprocessing import Queue

#class TestFTPBroker(unittest.TestCase):
#    def setUp(self):
#        """Sets up each unit test."""
#        db_file_name = "data/weather.db"
#        self._existing_data_directory = "C:\\Users\\Ralf\\Documents\\test"
#        self._not_existing_data_directory = "" # this a non-existing fake directory
#        self._temp_data_directory = "C:\\Users\\Ralf\\Documents\\test\\temp"
#        self._data_file_extension = ".ZIP"
#        self._delta_time = 10

#        self._sql_database_service_factory = SQLDatabaseServiceFactory(db_file_name)
#        self._exception_queue = Queue()


#    def tearDown(self):
#        """Finishes each unit test."""

#    def _on_message(self, message):
#        print(message.get_message())

#    def test_proxy(self): # TODO: implement the test
#        with FTPServerSideProxy(self._sql_database_service_factory, self._existing_data_directory, self._data_file_extension, self._temp_data_directory, self._on_message, self._exception_queue, self._delta_time) as proxy:
#            pass
#            ## stall the main thread until the program is finished
#            #exception_from_subprocess = []
#            #try:
#            #    exception_from_subprocess = self._exception_queue.get()
#            #except KeyboardInterrupt:
#            #    pass

#            #if exception_from_subprocess:
#            #    exception_from_subprocess.re_raise()   


#    def test_invalid_data_file(self):
#        with self.assertRaises(IOError):
#            with FTPServerSideProxy(self._sql_database_service_factory, self._not_existing_data_directory, self._data_file_extension, self._temp_data_directory, self._on_message, self._exception_queue, self._delta_time) as proxy:
#                # stall the main thread until the program is finished
#                exception_from_subprocess = []
#                try:
#                    exception_from_subprocess = self._exception_queue.get()
#                except KeyboardInterrupt:
#                    pass

#                if exception_from_subprocess:
#                    exception_from_subprocess.re_raise()        


#class MockServerSideProxy(IServerSideProxy):
#    """Interface class for a weather server broker proxy testing mock"""

#    def __init__(self):
#        self._observers = [];


#    def register_listener(self, observer):
#        """ Registers a new listener.
#        :param observer:    new listener to be registered
#        :type observer:     IWeatherPersistenceService
#        """
#        self._observers.append(observer)


#    def remove_listener(self, observer):
#        self._observers.remove(observer)


#    def acknowledge_persistence(self, finished_ID):
#        print(finished_ID)


#    def on_data_received(self, message_ID, station_ID, data):
#        message = WeatherMessage(message_ID, station_ID, data)
#        self._notify_listeners(message)


#    def _notify_listeners(self, message):
#        for observer in self._observers:
#            observer.add_data(message)


#if __name__ == '__main__':
#    unittest.main()
