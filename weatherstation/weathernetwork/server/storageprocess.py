from weathernetwork.server.istorageprocess import IStorageProcess
from weathernetwork.server.database import WeatherDB
from weathernetwork.common.combisensorarray import CombiSensorArray
from weathernetwork.common.delayedexception import DelayedException

class StorageProcess(IStorageProcess):
    """Persistence operation class"""

    def storage_worker(self, db_file_name, message_queue, acknowledgement_queue, exception_handler):
        """ Stores the dataset in the database.
        """
        
        try:
            database = WeatherDB(db_file_name, CombiSensorArray.get_sensors())

            while True: 
                message = message_queue.get() # obtains a WeatherMessage object
                if message == None:
                    break

                data = message.get_data()
                station_ID = message.get_station_ID()
                message_ID = message.get_message_ID()

                # concurrent calls to the database are allowed
                database.add_dataset(station_ID, data)

                # trigger acknowledgment to the client
                acknowledgement_queue.put(message_ID)
        except Exception as e:
            exception_handler( DelayedException(e) )

