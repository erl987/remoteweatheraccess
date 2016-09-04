from weathernetwork.server.databaseservice import IDatabaseService, IDatabaseServiceFactory
from weathernetwork.server.database import WeatherDB
from weathernetwork.common.combisensorarray import CombiSensorArray
from weathernetwork.common.delayedexception import DelayedException

class SQLDatabaseService(IDatabaseService):
    """SQL weather database service"""
    def __init__(self, db_file_name):
        self._observers = []
        self._database = WeatherDB(db_file_name, CombiSensorArray.get_sensors())

    def add_data(self, message):
        """
        Stores the dataset in the database.
        """
        data = message.get_data()
        station_ID = message.get_station_ID()
        message_ID = message.get_message_ID()

        # concurrent calls to the database are allowed
        self._database.add_dataset(station_ID, data)

        # trigger acknowledgment to the client
        self._notify_observers(message_ID)


    def register_observer(self, observer):
        """Registers a new observer.
        """
        self._observers.append(observer)


    def unregister_observer(self, observer):
        self._observers.remove(observer)


    def _notify_observers(self, finished_ID):
        for observer in self._observers:
            observer.acknowledge_persistence(finished_ID)
        

class SQLDatabaseServiceFactory(IDatabaseServiceFactory):
    """Factory for weather database services"""
    def __init__(self, db_file_name):
        self._db_file_name = db_file_name


    def create(self):
        return SQLDatabaseService(self._db_file_name)