import unittest
from weathernetwork.server.mockserversideproxy import MockServerSideProxy
from weathernetwork.server.weatherpersistenceservice import WeatherPersistenceService
from weathernetwork.common.weatherdataset import WeatherDataset
from weathernetwork.common.combisensordataset import CombiSensorDataset
from datetime import datetime
import time
from weathernetwork.server.storageprocess import StorageProcess

class Test_ftp_broker_test(unittest.TestCase):
    def test_ftp_broker(self):
        db_file_name = "data/weather.db"

        server_proxy = MockServerSideProxy()
        storage_process = StorageProcess()
        with WeatherPersistenceService(server_proxy, storage_process, db_file_name) as persistenceService:
            # generate test data
            station_ID = "TES2"
            message_ID = 12345
            data = WeatherDataset( datetime.utcnow(), [ CombiSensorDataset("OUT1", 30.9, 89.3) ], 532.3, 1024.3, 9.8, 341.4, 34.2, 10.9, 21.9)
           
            server_proxy.on_data_received(message_ID, station_ID, data)

            time.sleep(2) # wait for 2 seconds
            persistenceService.check_for_exceptions_in_processes()


if __name__ == '__main__':
    unittest.main()
